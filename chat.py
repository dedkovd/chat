import tornado, tornado.web, tornado.escape, tornado.websocket
from dal import DAL

def wsauth(handler_class):
    def wrap_open(handler_open, **kwargs):
        def check_token(handler, kwargs):
            auth = handler.request.query

            if auth:
                parts = auth.split('=')

                if len(parts) != 2 or parts[0].lower() != 'token':
                    return False

                token = parts[1]
                user_id = DAL().get_user_id_by_token(token)
                if user_id:
                    handler.user_id = user_id
                else:
                    return False
            else:
                return False

            return True

        def _open(self, *args, **kwargs):
            if check_token(self, kwargs):
                return handler_open(self, *args, **kwargs)
            else:
                self.close()
                return None
        
        return _open

    handler_class.open = wrap_open(handler_class.open)
    return handler_class

@wsauth
class ChatHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.application.openedSockets[self.user_id] = self
        self.send_broadcast('connStatus')

    def send_message_to_user(self, user_id, message):
        socket = self.application.openedSockets[str(user_id)]
        if socket:
            socket.write_message(message)

    def send_broadcast(self, message):
        for user_id in self.application.openedSockets:
            if user_id <> self.user_id:
                socket = self.application.openedSockets[user_id]
                socket.write_message(message)

    def on_message(self, message):
        message = DAL().save_message(self.user_id, message)
        if message['to']['user_id'] == -1:
           self.send_broadcast(message)
        else:
            self.send_message_to_user(message['to']['user_id'], message)

    def on_close(self, message=None):
        self.send_broadcast('connStatus')
        del self.application.openedSockets[self.user_id]

class ActiveUsersHandler(tornado.web.RequestHandler):
    def get(self):
        active_users_id = self.application.openedSockets.keys()
        if active_users_id:
            users_list = DAL().get_users(active_users_id)
            self.write(tornado.escape.json_encode(users_list))
        else:
            self.write('[]')

class AuthHandler(tornado.web.RequestHandler):
    def get_user(self, login):
        self.user_id = DAL().get_user_id_by_login(login)
        if not self.user_id:
            self.set_status(400)
            self.finish('{"error": "User not found"}')
            return None

        return DAL().get_user(self.user_id)
        
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        self.user = self.get_user(data['login'])
        if self.user is None:
            return

        if DAL().check_password(self.user['user_id'], data['password']):
            result = tornado.escape.json_encode({'token': DAL().generate_token(self.user_id)})
            self.finish(result)
            return
        
        self.set_status(401)
        self.finish('{"error": "Unauthorized"}')

class RegisterHandler(tornado.web.RequestHandler):
    def _finish_with_error(self, error):
        self.set_status(400)
        self.finish('{"error": "%s"}' % error)

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if DAL().check_user_login(data['login']):
            self._finish_with_error('Login already exists')
            return

        if DAL().check_user_email(data['email']):
            self._finish_with_error('E-Mail already exists')
            return
        
        DAL().save_user(data)

app = tornado.web.Application([
    (r"/register", RegisterHandler),
    (r"/auth", AuthHandler),
    (r"/active", ActiveUsersHandler),
    (r"/chat", ChatHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static/'}),
    ])
app.openedSockets = {}

if __name__ == "__main__":
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
