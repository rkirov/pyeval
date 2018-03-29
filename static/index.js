
(function() {
var poller, editor;

/**
 * A simple querystring parser.
 * Example usage: var q = $.parseQuery(); q.fooreturns  'bar' if query contains
'?foo=bar'; multiple values are added to an array.
 */
function getParameterByName(name) {
  name = name.replace(/[\[]/, '\\\[').replace(/[\]]/, '\\\]');
  var regexS = '[\\?&]' + name + '=([^&#]*)';
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  if (results == null) {
    return '';
  } else {
    return decodeURIComponent(results[1].replace(/\+/g, ' '));
  }
}

function Poller(idin, waittimein) {
  this.id = idin;
  this.waittime = waittimein || 1000;
  this.setTimeout = setTimeout(poll, waittimein);
}

function poll() {
  $.ajax({
    url : '/exec',
    data : {id : poller.id},
    success : function(raw_data) {
      data = JSON.parse(raw_data);
      if (data.status !== 'not ready') {
        $('#permalink')
            .html('<a href="index.html?id=' + poller.id + '">permlink</a>');
        $('#loader').hide();
        $('#answer').show();
        $('#answer').html(data.output);
      } else {
        poller.settimeout = setTimeout(poll, poller.waittime);
      }
    }
  });
}

function execute(input) {
  var input = input || editor.getValue();
  // var input = input || $('#input').val();
  // console.log('exec', input);
  $.ajax({
    url : '/exec',
    type : 'POST',
    data : {input : input},
    success : function(data) {
      /* console.log('entered with id', data); */
      poller = new Poller(data);
      $('#loader').show();
      $('#input').attr('disabled', 'disabled');
    }
  });
}

$(document).ready(function() {
  editor = CodeMirror.fromTextArea(document.getElementById('input'), {
    mode : {name : 'python', version : 2, singleLineStringErrors : false},
    lineNumbers : true,
    indentUnit : 4,
    tabMode : 'shift',
    matchBrackets : true,
    onKeyEvent : function(editor, e) {
      if (e.keyCode === 13 && e.shiftKey) {
        execute();
        e.stop();
      }
    }
  });
  $('#loader').hide();
  $('#compute_button').click(function() { execute(); });
  var id = getParameterByName('id');
  if (id) {
    $.ajax({
      url : '/get_id',
      type : 'GET',
      data : {id : id},
      success : function(raw_data) {
        data = JSON.parse(raw_data);
        editor.setValue(data.exec_string);
      }
    });
    poller = new Poller(id);
  }
});
})();
