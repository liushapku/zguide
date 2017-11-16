//$ = require('jquery')
$(document).ready(function(){
    var worker;

    if(typeof(worker) == "undefined"){
        worker = new Worker(workerurl);
    }
    worker.onmessage = function(event){
        data = event.data
        console.log('-----------')
        console.log(data)
        switch(data.event){
            case "receive":
                alert(data.from + ' says:\n' + data.message)
                break;
            case "friend disconnected":
                alert(data.name + ' is disconnected')
                break;
            default:
                console.error('unknown event received: ' + data.event)
                break;
        }
    }
    console.log('Connecting to WebWorker')
    worker.postMessage({
        event: 'init',
        scripts: ["https://cdnjs.cloudflare.com/ajax/libs/socket.io/2.0.3/socket.io.js"],
    });

    var messagebox = $('#messagebox');
    var sendbutton = $('#sendbutton');
    var receiverbox = $('#receiverbox');
    sendbutton.click(function(){
        message = messagebox.val()
        receiver = receiverbox.val()
        if (message && receiver){
            worker.postMessage({
                event: 'send',
                to: receiver,
                message: message,
            });
        }
    });

    var fetchbutton = $('#fetchbutton')
    var fetchbox = $('#fetchbox')
    fetchbox.change(function(){
        console.log(fetchbox[0].scrollHeight);
    })


    //Store the XHR in a closure.
    function xhrProvider() {
        var xhr = $.ajaxSettings.xhr();
        //Do what you want with the XHR Object. For Example:
        xhr.onreadystatechange = function(){
            if (xhr.readyState == 3 || xhr.readyState == 4) {
                fetchbox.html(xhr.responseText);
                fetchbox.scrollTop(fetchbox[0].scrollHeight);
                console.log(xhr.readyState, xhr.responseText);
            }
        }
        return xhr;
    }

    //Then when using $.ajax specifiy a custom xhr like this:
    fetchbutton.click(function(){
        var ajaxRequest = $.ajax({
            type: 'get',
            url: '/gevent',
            data: {},
            dataType: 'text/html',
            //processData: false,
            xhr: xhrProvider
        });
    })
});
