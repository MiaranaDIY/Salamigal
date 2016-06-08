var socketService = new SocketService();

function mapObject(object, callback) {
  return Object.keys(object).map(function (key) {
    return callback(key, object[key]);
  });
};

var Salamigal = React.createClass({
  displayName: 'Salamigal',
  render: function() {
    var Selector = Salamigal.Selector;
    return (
      <div>
        <Selector socketService={this.props.socketService} />
      </div>
    );
  }
});

Salamigal.Selector = React.createClass({
  displayName: 'Salamigal.Selector ',
  getInitialState: function () {
    return { value: '',data: [],selectedDevice: [{group: {label: '-', value: '-'}}], global: {streaming:0} };
  },
    requestDeviceList: function () {
        var FID = 'requestDeviceList';
        this.setState({data: []});
        var socket = this.props.socketService;

        socket.sendRequest({task: 'command', cmd: 'req_dev', arg: '*'}, function (message) {
            this.setState({data: message.data.dev});
            var options = [];
            options.push({label: '--- All Devices ---', value: '*'});
            $.each(this.state.data, function (i, item) {
                options.push({label: item.location.value + ' - ' + item.name.value, value: item.uid.value});
            });
            this.setState({options: options});
            this.setState({selectedDevice: message.data.dev}); 
        }.bind(this),'requestDeviceList');
    },
  componentWillMount: function (){
    this.requestDeviceList();
  },
  updateValue: function (value) {
    if(value != null){
      this.setState({ value: value }); 
      var socket = this.props.socketService;
      socket.sendRequest({task: 'command',cmd: 'req_dev', arg: value.value}, function (message) {
          this.setState({selectedDevice: message.data.dev}); 
      }.bind(this),'updateValue');
    }
    else{
      this.setState({ value: {label: '', value: ''} });
    }
  },
  reloadValue: function (){
    this.requestDeviceList();
  },
  handleOnParamChange: function(e){
    var socket = this.props.socketService;
    socket.sendRequest({task: 'command', cmd: 'set_dev', arg: {uid: e.uid, param: e.param, val: e.value}}, function (message) {
        this.setState({ selectedDevice: message.data.dev }); 
        this.setState({ value: message.data.dev[0].uid.value }); 
        this.setState({ global: message.data.global });
    }.bind(this),'handleOnParamChange');
  },
  handleOnRefreshSelected: function(e){
    var socket = this.props.socketService;
    socket.sendRequest({task: 'command', cmd: 'req_dev', arg: e.uid}, function (message) {
      if (message.$type === 'complete') {
        this.setState({selectedDevice: message.data.dev}); 
      }
    }.bind(this),'handleOnRefreshSelected');
  },
  render: function () {
    var Card = Salamigal.Viewer.Card;
    return(
      <div>
      <Select name='device-selector' options={this.state.options} onChange={this.updateValue} value={this.state.value}>
      </Select>
      {/**<Dv.Table dev={this.state.selectedDevice} onStateChange={this.handleOnStateChange} onRefreshSelected={this.handleOnRefreshSelected}/>**/}
      <Card dev={this.state.selectedDevice} global={this.state.global} onParamChange={this.handleOnParamChange} onRefreshSelected={this.handleOnRefreshSelected} />
      </div>
    );
  }
});    
    
Salamigal.Viewer = React.createClass({
  displayName: 'Salamigal.Viewer',
  propTypes:{
    dev: React.PropTypes.array
  },
  getDefaultProps: function(){
    return {dev: [{group: {label: '-', value: '-'}}]};
  },
  render: function(){
    return (
      <div className="deviceViewer " />
    );
  }
});

Salamigal.Viewer.Button = React.createClass({
    displayName: 'Salamigal.Viewer.Button',
    propTypes: {
        onClick: React.PropTypes.func,
        type: React.PropTypes.string,
        state: React.PropTypes.number
    },
    handleOnClick: function(e){
        if (typeof this.props.onClick === 'function') {
            this.props.onClick(e);
        }
    },
    formatterClassName(type, state){
        switch(type){
            case "refresh":
                return "btn btn-default btn-refresh";
                break;
            case "switch":
                if(state == 1){
                    return "btn btn-success btn-switch";
                }
                else{
                    return "btn btn-danger btn-switch";
                }
                break;
            case "stream":
                if(state == 1){
                    return "btn btn-info btn-stream";
                }
                else{
                    return "btn btn-warning btn-stream";
                }
                break;
            default:
                return "btn btn-default" + type;
        }
    },
    formatterText(type, state){
                switch(type){
            case "refresh":
                return "Refresh";
                break;
            case "switch":
                if(state == 1){
                    return "Turn OFF";
                }
                else{
                    return "Turn ON";
                }
                break;
            case "stream":
                if(state == 1){
                    return "Stop Stream";
                }
                else{
                    return "Start Stream";
                }
                break;
            default:
                return type + ': ' + state;
        }
    },
    render: function(){
        return(
            <button onClick={this.handleOnClick} className={this.formatterClassName(this.props.type, this.props.state)}>{this.formatterText(this.props.type, this.props.state)}</button>
        );
    }
});

Salamigal.Viewer.Card = React.createClass({
  displayName: 'Salamigal.Viewer.Card ',
  propTypes:{
    dev: React.PropTypes.array,
    onParamChange: React.PropTypes.func,
    onRefreshSelected: React.PropTypes.func
  },
  getDefaultProps: function(){
    return {dev: [{group: {label: '-', value: '-'}}], global: {streaming: 0}};
  },
  handleOnParamChange: function(e){
    this.props.onParamChange(e);
  },
  handleOnRefreshSelected: function(e){
    this.props.onRefreshSelected(e);
  },
  handleOnStreamAll: function(e){
      var query = {uid: '*', param: 'stream', value: !this.props.global.streaming ? 1 : 0};
      this.props.onParamChange(query);
  },
  render: function(){
    var CardRow = Salamigal.Viewer.Card.Row;
    var Relay = Salamigal.Relay;
    var Ds18b20 = Salamigal.Ds18b20;
    var Hcsr04 = Salamigal.Hcsr04;
    var Button = Salamigal.Viewer.Button;
    if(this.props.dev.length == 1){
        return (
            <div className="viewer-card-container">
            {this.props.dev.map(function(device, i){
                return <CardRow deviceProperty={device} key={i} />
            })}
            {(() => {
              switch (this.props.dev[0].group.value) {
                case "DS18B20":   return <Ds18b20 deviceProperty={this.props.dev[0]} onParamChange={this.handleOnParamChange} onRefreshSelected={this.handleOnRefreshSelected}/>
                case "Relay":   return <Relay deviceProperty={this.props.dev[0]} onParamChange={this.handleOnParamChange} onRefreshSelected={this.handleOnRefreshSelected}/>
                case "HCSR04":   return <Hcsr04 deviceProperty={this.props.dev[0]} onParamChange={this.handleOnParamChange} onRefreshSelected={this.handleOnRefreshSelected}/>
              }
            })()}
            </div>
        );
    }
    else{
        return (
            <div className="viewer-card-container">
            <ul className="list-inline list-unstyled">
                <li><Button onClick={() => this.handleOnStreamAll('*')} type={'stream'} state={this.props.global.streaming ? 1 : 0}/></li>
             </ul>
            {this.props.dev.map(function(device, i){
                return <CardRow deviceProperty={device} key={i} />;
            })}
            </div>
        );
    }
  }
});

Salamigal.Viewer.Card.Row = React.createClass({
  displayName: 'Salamigal.Viewer.Card.Row',
  propTypes: {
    deviceProperty: React.PropTypes.object
  }, 
  getDefaultProps: function(){
    return {deviceProperty: {group: {label: '-', value: '-'}}};
  },
  render: function(){
    var CardCol = Salamigal.Viewer.Card.Col;
    return (
        <div className="viewer-card">
            {mapObject(this.props.deviceProperty, function (key, value) {
              return <CardCol label={value.label} value={value.value} key={key} />;
            })}
        </div>        
    );
  }
});

Salamigal.Viewer.Card.Col = React.createClass({
  displayName: 'Salamigal.Viewer.Card.Col',
  propTypes:{
    label: React.PropTypes.oneOfType([
      React.PropTypes.string,
      React.PropTypes.number
    ]),
    value: React.PropTypes.oneOfType([
      React.PropTypes.string,
      React.PropTypes.number
    ])
  },
  getDefaultProps: function(){
    return {label: '-', value: '-'};
  },
  render: function(){
    var CardLabel = Salamigal.Viewer.Card.Label;
    var CardValue = Salamigal.Viewer.Card.Value;
    return (
        <div className="row card-row">
          <div className="col-xs-5 card-col">
                <CardLabel label={this.props.label} />
          </div>
          <div className="col-xs-7 card-col">
                <CardValue value={this.props.value} />
          </div>
        </div>
    );
  }
});

Salamigal.Viewer.Card.Label = React.createClass({
  displayName: 'Salamigal.Viewer.Card.Label',
  propTypes:{
    label: React.PropTypes.oneOfType([
      React.PropTypes.string,
      React.PropTypes.number
    ])
  },
  getDefaultProps: function(){
    return {label: '-'};
  },
  render: function(){
    return (
      <div className="card-label">{this.props.label + ':'}</div>
    );
  }
});

Salamigal.Viewer.Card.Value = React.createClass({
  displayName: 'Salamigal.Viewer.Card.Value',
  propTypes:{
    value: React.PropTypes.oneOfType([
      React.PropTypes.string,
      React.PropTypes.number
    ])
  },
  getDefaultProps: function(){
    return {value: '-'};
  },
  render: function(){
    return (
      <div className="card-value">{this.props.value}</div>
    );
  }
});

Salamigal.Relay = React.createClass({
  displayName: 'Salamigal.Relay',
  propTypes: {
        deviceProperty: React.PropTypes.object,
        onParamChange: React.PropTypes.func,
        onRefreshSelected: React.PropTypes.func
  },
  getDefaultProps: function() {
    return {deviceProperty: {group: {label: '-', value: '-'}}};
  },
  handleOnParamChange: function(e){
    if (typeof this.props.onParamChange === 'function') {
        var clickData = {
            param: e,
            value: !this.props.deviceProperty[e].value ? 1 : 0, 
            uid: this.props.deviceProperty.uid.value
         };
        this.props.onParamChange(clickData);
    }
  },
  handleOnRefreshSelected: function(e){
    if (typeof this.props.onRefreshSelected === 'function') {
      this.props.onRefreshSelected({uid: this.props.deviceProperty.uid.value});
    }
  },
  render: function() {
    var Button = Salamigal.Viewer.Button;
    return (
      <ul className="list-inline list-unstyled">
        <li><Button onClick={() => this.handleOnParamChange('state')}  type={'switch'} state={this.props.deviceProperty.state.value ? 1 : 0}/></li>
        <li><Button onClick={this.handleOnRefreshSelected} type={'refresh'} state={this.props.deviceProperty.state.value ? 1 : 0}/></li>
        <li><Button onClick={() => this.handleOnParamChange('stream')} type={'stream'} state={this.props.deviceProperty.stream.value ? 1 : 0}/></li>
      </ul>
    );
  }
});

Salamigal.Ds18b20 = React.createClass({
  displayName: 'Salamigal.Ds18b20',
  propTypes: {
        deviceProperty: React.PropTypes.object,
        onParamChange: React.PropTypes.func,
        onRefreshSelected: React.PropTypes.func
  },
  getDefaultProps: function() {
    return {deviceProperty: {group: {label: '-', value: '-'}}};
  },
  handleOnParamChange: function(e){
    if (typeof this.props.onParamChange === 'function') {
        var clickData = {
            param: e,
            value: !this.props.deviceProperty[e].value ? 1 : 0, 
            uid: this.props.deviceProperty.uid.value
         };
        this.props.onParamChange(clickData);
    }
  },
  handleOnRefreshSelected: function(e){
    if (typeof this.props.onRefreshSelected === 'function') {
      this.props.onRefreshSelected({uid: this.props.deviceProperty.uid.value});
    }
  },
  render: function() {
    var Button = Salamigal.Viewer.Button;
    return (
      <ul className="list-inline list-unstyled">
        <li><Button onClick={this.handleOnRefreshSelected} type={'refresh'} state={this.props.deviceProperty.stream.value ? 1 : 0}/></li>
        <li><Button onClick={() => this.handleOnParamChange('stream')} type={'stream'} state={this.props.deviceProperty.stream.value ? 1 : 0}/></li>
      </ul>
    );
  }
});

Salamigal.Hcsr04 = React.createClass({
  displayName: 'Salamigal.Hcsr04',
  propTypes: {
        deviceProperty: React.PropTypes.object,
        onParamChange: React.PropTypes.func,
        onRefreshSelected: React.PropTypes.func
  },
  getDefaultProps: function() {
    return {deviceProperty: {group: {label: '-', value: '-'}}};
  },
  handleOnParamChange: function(e){
    if (typeof this.props.onParamChange === 'function') {
        var clickData = {
            param: e,
            value: !this.props.deviceProperty[e].value ? 1 : 0, 
            uid: this.props.deviceProperty.uid.value
         };
        this.props.onParamChange(clickData);
    }
  },
  handleOnRefreshSelected: function(e){
    if (typeof this.props.onRefreshSelected === 'function') {
      this.props.onRefreshSelected({uid: this.props.deviceProperty.uid.value});
    }
  },
  render: function() {
    var Button = Salamigal.Viewer.Button;
    return (
      <ul className="list-inline list-unstyled">
        <li><Button onClick={this.handleOnRefreshSelected} type={'refresh'} state={this.props.deviceProperty.stream.value ? 1 : 0}/></li>
        <li><Button onClick={() => this.handleOnParamChange('stream')} type={'stream'} state={this.props.deviceProperty.stream.value ? 1 : 0}/></li>
      </ul>
    );
  }
});

ReactDOM.render(
  <Salamigal socketService={socketService}/>,
  document.getElementById('content')
);
