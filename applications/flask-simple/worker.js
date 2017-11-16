var socket;
console.log(socket)

self.onmessage = function(msg){
    switch(msg.data.event){
        case "init":
            if(socket)
                return
            console.log(location.origin);
            console.log(msg.data.scripts)
            importScripts(msg.data.scripts)
            console.log('connecting socket')
            socket = io(location.origin);

            socket.on('connect', function(){
                console.log('socket connected')
                //socket.emit('client_connected', {data: 'New client!'});
            });
            socket.on('disconnect', function(){
                console.log('Disconnected');
            });
            socket.on('message', (msg) => {
                console.log('*** ' + msg)
                postMessage(JSON.parse(msg));
            });
            break;
        case "send":
            delete msg.data["event"]
            if(socket){
                socket.send(msg.data)
            }
            break;
        default:
            if(socket){
                console.error('unknown event' + msg.data.event);
            }
            break;
    }
}
