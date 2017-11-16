$(document).ready(function(){
    var output = $('#output')
    var sendbtn = $('#sendbutton')
    var message = $('#message')
    var close = $('#closebutton')

    var ws_url = location.protocol.replace('http', 'ws') + "//" + location.host + "/echo/channel";
    console.log(ws_url)
    var socket = new WebSocket(ws_url);
    console.log(socket)
    socket.onopen = function (event) {
      socket.send("Here's some text that the server is urgently awaiting!");
    };
    socket.onmessage = function (event) {
        console.log(event.data)
        output.append(event.data + '<br/>')
    };
    socket.onclose = function (event) {
        console.log(event.data)
        output.append('=== connection closed ===' + '<br/>')
    }
    sendbtn.click(function(){
        if (message.val()){
            console.log(socket.readyState)
            if (socket.readyState == 1){
                console.log('=== sending ' + message.val());
                socket.send(message.val())
            }else if(socket.readyState == 3){
                output.append('! socket is closed<br/>')
            }
        }
    })
    close.click(function(){
        socket.close()
    })
})
