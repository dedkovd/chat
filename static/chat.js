var chatApp = angular.module('chatApp', []);

chatApp.controller('ChatController', function ChatController($scope, $http) {
	$scope.connectionStatus = 'Disconnected';	
	$scope.messages = [];
	$scope.recipient = '-1';

	$scope.loadUsers = function() {
		$http.get("/active").then(function(response) {
			$scope.users = response.data;
		});
	};
	$scope.loadUsers();

	$scope.loginToChat = function(login) {
		data = {'login': $scope.userLogin, 'password': $scope.userPassword};
		$http.post("/auth",data).then(function(response) {
			$scope.token = response.data['token'];
			$scope.connectToChat();
			$scope.loadUsers();
		});
	};

	$scope.connectToChat = function() {
		if (!$scope.token) {
			return;
		};
		
		$scope.chat = new WebSocket("ws://localhost:8888/chat?token="+$scope.token);
		$scope.chat.onopen = function() {
			$scope.connectionStatus = 'Connected';
		};
		$scope.chat.onclose = function() {
			$scope.connectionStatus = 'Disconnected';
		};
		$scope.chat.onmessage = function(message) {
			var data = message.data;
			if (data == 'connStatus') {
				$scope.loadUsers();
			} else {
				msg = angular.fromJson(data)
				$scope.messages.push(msg);
				$scope.$apply();
			}

		}
	};

	$scope.sendMessage = function() {
		if (!$scope.recipient) {
			$scope.recipient = -1;
		};

		$scope.chat.send('{"to": '+$scope.recipient+
			', "text": "'+$scope.messageText+'"}');
		msg = {from: {login: "Me"}, to: $scope.recipient, text: $scope.messageText}
		$scope.messages.push(msg);
	}
});
