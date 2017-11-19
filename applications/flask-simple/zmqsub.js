$(document).ready(function(){
  var output = $('#output')
  var close = $('#closebutton')

  var ws_url = location.protocol.replace('http', 'ws') + "//" + location.host + "/zmqsub/stream";
  //var ws_url = location.protocol.replace('http', 'ws') + "//" + location.host + "/zmqsub/stream";
  console.log(ws_url)
  var socket = new WebSocket(ws_url);
  console.log(socket)
  socket.onmessage = function (event) {
    console.log(event.data)
    output.append(event.data + '<br/>')
  };
  socket.onclose = function (event) {
    console.log(event.data)
    output.append('=== connection closed ===' + '<br/>')
  }
  close.click(function(){
    console.log('socket closed')
    //socket.send('close')
    socket.close()
  })
})
