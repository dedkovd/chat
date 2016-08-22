import redis

class DAL(object):
	srv = redis.Redis()

	def getUser(self, user_id):
		if not self.srv.hexists('users', user_id):
			return None

		u = eval(self.srv.hget('users', user_id))
		del u['password']
		u['user_id'] = user_id
		return u

