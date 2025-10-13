var checkout = {};

$(document).ready(function() {
  var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

  $(window).load(function() {
    $messages.mCustomScrollbar();
    insertResponseMessage('Hi there, I\'m your personal Concierge. How can I help?');
  });

  function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar('scrollTo', 'bottom', {
      scrollInertia: 10,
      timeout: 0
    });
  }

  function setDate() {
    d = new Date()
    if (m != d.getMinutes()) {
      m = d.getMinutes();
      $('<div class="timestamp">' + d.getHours() + ':' + m + '</div>').appendTo($('.message:last'));
    }
  }

/*
  function callChatbotApi(message) 
  {
  const apiUrl = "https://4f5cm86az3.execute-api.us-east-2.amazonaws.com/Prod1/chatbot";
  return fetch(apiUrl, 
    {
    method: "POST",
    headers: 
    {"Content-Type": "application/json"},
    body: JSON.stringify({
    messages: [{
      type: "unstructured",
      unstructured: {
      text: message}}]
    })
  })
  .then(response => response.json())
  .then(data => ({ data }))  // mimic SDK response.data structure
  .catch(error => {
    console.error("API call error:", error);
    throw error;
  });
  }
*/

function callChatbotApi(message) {
  const apiUrl = "https://4f5cm86az3.execute-api.us-east-2.amazonaws.com/Prod1/chatbot";
  
  return fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [{
        type: "unstructured",
        unstructured: { text: message }
      }]
    })
  })
  .then(response => response.json())
  .then(data => {
    // Parse the stringified JSON in the "body"
    let parsedBody;
    try {
      parsedBody = JSON.parse(data.body);
    } catch (e) {
      console.error("Failed to parse body:", e);
      parsedBody = {};
    }

    //Return in the same structure expected by insertMessage()
    return { data: parsedBody };
  })
  .catch(error => {
    console.error("API call error:", error);
    throw error;
  });
}



  function insertMessage() {
    msg = $('.message-input').val();
    //Debug prompt 
    console.log("XXXXXX User typed message:", msg, "    XXXXXX");

    if ($.trim(msg) == '') {
      return false;
    }
    $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
    setDate();
    $('.message-input').val(null);
    updateScrollbar();

    callChatbotApi(msg)
      .then((response) => {
        console.log(response);
        var data = response.data;

        if (data.messages && data.messages.length > 0) {
          console.log('received ' + data.messages.length + ' messages');

          var messages = data.messages;

          for (var message of messages) {
            if (message.type === 'unstructured') {

              //Debug prompt
              console.log("YYYYYY Chatbot API Response Text:", message.unstructured.text, "    YYYYYY");

              insertResponseMessage(message.unstructured.text);
            } else if (message.type === 'structured' && message.structured.type === 'product') {
              var html = '';

              insertResponseMessage(message.structured.text);

              setTimeout(function() {
                html = '<img src="' + message.structured.payload.imageUrl + '" witdth="200" height="240" class="thumbnail" /><b>' +
                  message.structured.payload.name + '<br>$' +
                  message.structured.payload.price +
                  '</b><br><a href="#" onclick="' + message.structured.payload.clickAction + '()">' +
                  message.structured.payload.buttonLabel + '</a>';
                insertResponseMessage(html);
              }, 1100);
            } else {
              console.log('not implemented');
            }
          }
        } else {
          insertResponseMessage('Oops, something went wrong. Please try again.');
        }
      })
      .catch((error) => {
        console.log('an error occurred', error);
        insertResponseMessage('Oops, something went wrong. Please try again.');
      });
  }

  $('.message-submit').click(function() {
    insertMessage();
  });

  $(window).on('keydown', function(e) {
    if (e.which == 13) {
      insertMessage();
      return false;
    }
  })

  function insertResponseMessage(content) {
    $('<div class="message loading new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    setTimeout(function() {
      $('.message.loading').remove();
      $('<div class="message new"><figure class="avatar"><img src="https://media.tenor.com/images/4c347ea7198af12fd0a66790515f958f/tenor.gif" /></figure>' + content + '</div>').appendTo($('.mCSB_container')).addClass('new');
      setDate();
      updateScrollbar();
      i++;
    }, 500);
  }

});
