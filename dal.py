import redis
import uuid
import hashlib

class DAL(object):
	srv = redis.Redis()

	def _prepare_user(self, user, user_id):
		u = eval(user)
		del u['password']
		return u

	def get_user(self, user_id):
		if user_id == -1:
			return {'login': 'All users', 'email': '', 'user_id': -1}

		if not self.srv.hexists('users', user_id):
			return None
		else:
			user = self.srv.hget('users', user_id)
			return self._prepare_user(user, user_id)

	def check_password(self,user_id,password):
		user = eval(self.srv.hget('users', user_id))
		phash = hashlib.sha224(password).hexdigest()
		return user["password"] == phash

	def save_user(self, user):
		uid = self.srv.incr('user:id')
		user['user_id'] = uid
        	user['password'] = hashlib.sha224(user['password']).hexdigest()
		self.srv.hset('users',uid,user)
		self.srv.hset('logins',user['login'],uid)
		self.srv.hset('emails',user['email'],uid)

	def get_user_id_by_login(self, login):
		return self.srv.hget('logins', login)

	def check_user_login(self, login):
		return self.srv.hexists('logins', login)

	def check_user_email(self, email):
		return self.srv.hexists('emails', email)

	def get_users(self, users_id):
		users = self.srv.hmget('users', users_id)
		u = lambda u, uid: self._prepare_user(u,uid)
		res = [self._prepare_user(u,i) for u,i in zip(users,users_id)]
		return res

	def generate_token(self, user_id):
		token = str(uuid.uuid1())
		self.srv.hset('tokens', token, user_id)
		return token

	def get_user_id_by_token(self, token):
		return self.srv.hget('tokens', token)

	def save_message(self, user_id, message):
		message = eval(message)
		message['from'] = self.get_user(user_id)
		message['to'] = self.get_user(message['to'])		
		self.srv.lpush('messages', message)
		return message
	

