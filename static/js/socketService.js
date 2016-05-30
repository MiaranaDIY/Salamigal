'use strict';
var sid = '*';
function SocketService() {
	var service = {};

	var pendingCallbacks = {};
	var currentMessageId = 0;

	var ws = new ReconnectingWebSocket("ws://" + window.location.hostname + '/ws' + (location.port ? ':' + location.port : ''));
	var preConnectionRequests = [];
	var connected = false;
    
    ws.onerror = function (error) {
        console.log(error);
        $('#conn-indicator').css('color','yellow');
        if (confirm('Server disconnected. Reload page?')) {
            window.location.reload(true); 
        } 
    };

	ws.onopen = function () {
        $('#conn-indicator').css('color','yellow');
        //Send init request
        var r = {
            'task': 'init',
            'cmd': '*',
            'arg': '*',
            'sid': '*'
        };
        r = JSON.stringify(r);
        ws.send(r);
		connected = true;
	};
    
    //On close
    ws.onclose = function (e) {
      $('#conn-indicator').css('color','red');
      connected = false;
    };

	ws.onmessage = function (message) {
        var data = JSON.parse(message.data);
        //console.log(data);
        if(data.init){
            sid = data.init.sid;
            $('#conn-indicator').css('color','lime');
        }
        listener(data);
        if (preConnectionRequests.length === 0 || sid == '*') return;
        
		//console.log('Sending (%d) requests', preConnectionRequests.length);
		for (var i = 0, c = preConnectionRequests.length; i < c; i++) {
            preConnectionRequests[i].sid = sid;
			ws.send(JSON.stringify(preConnectionRequests[i]));
		}
		preConnectionRequests = [];
	};

	function sendRequest(request, cb, streamMsgId) {
        request.sid = sid;
        if(streamMsgId){
            request.$id = streamMsgId;
        }
        else{
            request.$id = generateMessageId();
        }
        pendingCallbacks[request.$id] = cb;

		if (!connected) {
			console.log('Not connected yet, saving request', request);
			preConnectionRequests.push(request);
			return;
		}

		console.log('Sending request', request);
		ws.send(JSON.stringify(request));
	}

	function listener(message) {
		// If an object exists with id in our pendingCallbacks object, resolve it
		if (pendingCallbacks.hasOwnProperty(message.$id)){
			pendingCallbacks[message.$id](message);
        }
	}

	function requestComplete(id) {
		console.log("requestComplete:", id);
		delete pendingCallbacks[id];
	}

	function generateMessageId() {
		if (currentMessageId > 10000)
			currentMessageId = 0;

		return new Date().getTime().toString() + '~' + (++currentMessageId).toString();
	}
    
	service.sendRequest = sendRequest;
	service.requestComplete = requestComplete;
	return service;
}
