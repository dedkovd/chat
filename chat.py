import tornado, tornado.web, tornado.escape, tornado.websocket
import redis
import hashlib
import uuid

def wsauth(handler_class):
    def wrap_open(handler_open, **kwargs):
        def check_token(handler, kwargs):
            auth = handler.request.query

            if auth:
                parts = auth.split('=')

                if len(parts) != 2 or parts[0].lower() != 'token':
                    return False

                token = parts[1]
                user_id = srv.hget('tokens', token)
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

    def save_message(self, message):
        message['from'] = self.user_id
        srv.lpush('messages', message)

    def send_message_to_user(self, user_id, message):
        socket = self.application.openedSockets[user_id]
        if socket:
            socket.write_message(message)

    def send_broadcast(self, message):
        for user_id in self.application.openedSockets:
            if user_id <> self.user_id:
                socket = self.application.openedSockets[user_id]
                socket.write_message(message)

    def on_message(self, message):
        message = eval(message)
        self.save_message(message)
        if message['to'] == -1:
            self.send_broadcast(message['text'])
        else:
            self.send_message_to_user(message['to'], message['text'])

    def on_close(self, message=None):
        del self.application.openedSockets[self.user_id]

class ActiveUsersHandler(tornado.web.RequestHandler):
    def get(self):
        active_users_id = self.application.openedSockets.keys()
        if active_users_id:
            active_users = srv.hmget('users', active_users_id)
            users_list = []
            for user in active_users:
                users_list.append(eval(user))
            self.write(tornado.escape.json_encode(users_list))
        else:
            self.write('[]')

class AuthHandler(tornado.web.RequestHandler):
    def check_password(self, password):
        phash = hashlib.sha224(password).hexdigest()
        return self.user['password'] == phash

    def generate_token(self):
        token = str(uuid.uuid1())
        srv.hset('tokens', token, self.user_id)
        return token

    def get_user(self, login):
        self.user_id = srv.hget('logins', login)
        if not self.user_id:
            self.set_status(400)
            self.finish('{"error": "User not found"}')
            return None

        return eval(srv.hget('users', self.user_id))
        
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        self.user = self.get_user(data['login'])
        if self.user is None:
            return

        if self.check_password(data['password']):
            result = tornado.escape.json_encode({'token': self.generate_token()})
            self.finish(result)
            return
        
        self.set_status(401)
        self.finish('{"error": "Unauthorized"}')

class RegisterHandler(tornado.web.RequestHandler):
    def check_login(self, login):
        if srv.hexists('logins', login):
            self.set_status(400)
            self.finish('{"error": "Login already exists"}')
            return False

        return True

    def check_mail(self, mail):
        if srv.hexists('emails', mail):
            self.set_status(400)
            self.finish('{"error": "E-Mail already exists"}')
            return False

        return True

    def save_user(self, data):
        uid = srv.incr('user:id')
        srv.hset('users',uid,data) 
        srv.hset('logins',data['login'],uid)
        srv.hset('emails',data['email'],uid)

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if not self.check_login(data['login']):
            return

        if not self.check_mail(data['email']):
           return
        
        data['password'] = hashlib.sha224(data['password']).hexdigest()
        self.save_user(data)

app = tornado.web.Application([
    (r"/register", RegisterHandler),
    (r"/auth", AuthHandler),
    (r"/active", ActiveUsersHandler),
    (r"/chat", ChatHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static/'}),
    ])
app.openedSockets = {}

srv = redis.Redis()

if __name__ == "__main__":
    app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
