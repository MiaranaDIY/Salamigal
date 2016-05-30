jQuery(document).ready(function($) {
    //Smooth scroll
    $(function() {
      $('a[href*="#"]:not([href="#"])').click(function() {
        if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
          var target = $(this.hash);
          target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
          if (target.length) {
            $('html, body').animate({
              scrollTop: target.offset().top
            }, 1000);
            return false;
          }
        }
      });
    });

    var websocket = new WebSocket('ws://'+document.location.hostname+'/ws', ['soap', 'xmpp']);
    
    // When the websocket is open, send some data to the server
    websocket.onopen = function () {
      console.log("Websocket opened!");
      $('#conn-indicator').css('color','yellow');
      //Send init request
      r = {
            'task': 'init',
            'cmd': '*',
            'arg': '*',
            'id': '*'
        };
      r = JSON.stringify(r);
      send(r);
    };

    // One error
    websocket.onerror = function (error) {
        console.log(error);
        $('#conn-indicator').css('color','yellow');
        if (confirm('Server disconnected. Reload page?')) {
            window.location.reload(true); 
        } 
    };

    // On message
    websocket.onmessage = function (e) {
      //Parse data to JSON format
      data = JSON.parse(e.data);
      //console.log(data);
      //Get session id from init message & set connection indicator to connected (lime color)
      if(data.init){
        sid = data.init.sid;
        $('#conn-indicator').css('color','lime');        
        console.log("Websocket connected!");
        //get device list
        req_dev('*');
      }
      else if(data.dev){
        view_dev(data.dev);  
      }
    };
    
    //On close
    websocket.onclose = function (e) {
      $('#conn-indicator').css('color','red');
    };
    
    //Send to server
    send = function (v) {
        websocket.send(v);
        return v;
    };
    
    //Set device property
    set_dev = function(uid, param, val){
        q = {
            'task': 'command',
            'cmd': 'set_dev',
            'arg': {
                'uid': uid,
                'param': param,
                'val': val
            },
            'id': sid
        };
        q = JSON.stringify(q);
        send(q);  
    };
    
    //Display device information on panel
    view_dev = function(d){
        //Manually create group location
        var location = ['Kamar', 'Kamar Tamu'];
        //Update device list select box
        if(d.length > 1){
            //Match device group by location
            var options = '';
            $.each(location, function(i, loc){
                var pre = '<optgroup label="'+loc+'">';
                //loop tru device list
                $.each(d, function (i, item) {
                    if(item['location'] == loc){
                        pre += '<option value="'+item.uid+'" data-tokens="'+loc +' '+ item.name +'">'+item.name+'</option>';
                    }
                });
                options += pre + '</optgroup>';
            });
            $('#device-selector').html(options);
            $('#device-selector').selectpicker('refresh');
        }
        else if(d.length == 1){
            //Create device control
            $.each(d, function (i, dev) {
                //Control template for relay device type
                if(dev.group == 'Relay'){
                    if(dev.state == 0){
                        d[i]['control'] = '<button data-device-uid="'+dev.uid+'" data-device-state="'+dev.state+'" class="control-relay-switch btn btn-default">Switch</button>';
                    }
                    else{
                        d[i]['control'] = '<button data-device-uid="'+dev.uid+'" data-device-state="'+dev.state+'" class="control-relay-switch btn btn-success">Switch</button>';
                    }
                    if(dev.stream == 0){
                        d[i]['control'] += '<button data-device-uid="'+dev.uid+'" data-device-stream="'+dev.stream+'" class="control-relay-stream btn btn-default">Stream</button>';
                    }
                    else{
                        d[i]['control'] += '<button data-device-uid="'+dev.uid+'" data-device-stream="'+dev.stream+'" class="control-relay-stream btn btn-danger">Stream</button>';
                    }
                    d[i]['control'] += '<button data-device-uid="'+dev.uid+'" data-device-state="'+dev.state+'" class="control-relay-refresh btn btn-default">Refresh</button>';
                }
                //Control template for relay device type
                else if(dev.group == 'DS18B20'){
                    if(dev.stream == 0){
                        d[i]['control'] += '<button data-device-uid="'+dev.uid+'" data-device-stream="'+dev.stream+'" class="control-ds18b20-stream btn btn-default">Stream</button>';
                    }
                    else{
                        d[i]['control'] += '<button data-device-uid="'+dev.uid+'" data-device-stream="'+dev.stream+'" class="control-ds18b20-stream btn btn-danger">Stream</button>';
                    }
                    d[i]['control'] += '<button data-device-uid="'+dev.uid+'" data-device-state="'+dev.state+'" class="control-ds18b20-refresh btn btn-default">Refresh</button>';
                }
            });
            //Create device view & set device value in property panel
            $('#table-panel').bootstrapTable('load', d);
            $('#table-panel').bootstrapTable({
                data: d, 
                columns: [{
                    field: 'uid',
                    title: 'UID'
                },
                {
                    field: 'name',
                    title: 'Name'
                }, 
                {
                    field: 'location',
                    title: 'Location'
                }, 
                {
                    field: 'group',
                    title: 'Group'
                }]
            });
        }
    };
    
    //Request device information
    req_dev = function(d){
        q = {
            'task': 'command',
            'cmd': 'req_dev',
            'arg': d,
            'id': sid
        };
        q = JSON.stringify(q);
        send(q);
    };
    
    //Stream device data
    stream_start = function(uid){
        q = {
            'task': 'command',
            'cmd': 'stream_start',
            'arg': {
                'uid': uid
            },
            'id': sid
        };
        q = JSON.stringify(q);
        send(q);
    };
    
    //Stop devide data stream
    stream_stop = function(uid){
        q = {
            'task': 'command',
            'cmd': 'stream_stop',
            'arg': {
                'uid': uid
            },
            'id': sid
        };
        q = JSON.stringify(q);
        send(q);
    };
    
    
    /** Start Event Handler **/
    //Event device select
    $('#device-selector').on('change', function(){
        var selected = $(this).find("option:selected").val();
        req_dev(selected);
    });
    
    /** End Event Handler **/

}); 