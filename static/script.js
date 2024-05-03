// sendAjax
async function sendAjax(dataToSend) {
    try 
    {
        const response = await $.ajax({
            url: '/ask',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(dataToSend),
            success: function(response) {
                //console.log("Response: ", response);  // Log the response to debug
        
                
                $('#chat-box').append("<br><div id='reply' style='background-color:powderblue;'><strong>הומי: </strong>");

                if (response.reply && typeof response.reply === 'string' && response.reply.trim() !== '') {
                    $('#chat-box').append('<div>' + response.reply.trim() + '</div>');
                } else {
                    $('#chat-box').append('<div>Undefined or empty response</div>');
                }

                $('#chat-box').append("</div>");
                $('#chat-box').append("<br><br>");

            },
            error: function(error) {
                //console.log("Error:", error);
                $('#chat-box').append('<div>Error fetching response</div>');
            }
        });
        
    } 
    catch (error) 
    {
        alert('Error sending data');
        //console.error(error.responseText);
    }
}

// readFileAsDataURL
function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        var reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}


// document ready
$(document).ready(function() {

    // send-btn.click
    $('#send-btn').click(async function() {

        const userInput = $('#user-input').val().trim();
        const file      = $('#file-input')[0].files[0];

        var dataToSend  = { message: userInput };


        if (!userInput.trim() && !file)    
            return;

        // Append the user's message to the chat box with prefix
        $('#chat-box').append(`<div><strong>את/ה:</strong><br>${userInput}</div>`);

        // Clear the input field
        $('#user-input').val('');

        // TODO
        $('#file-input').val('');


        if (file) 
        {
            try {
                const fileData = await readFileAsDataURL(file);

                const base64String = fileData.replace(/^data:.+;base64,/, '');

                dataToSend.file = base64String;
                dataToSend.filename = file.name;
            } 
            catch (err) 
            {
                alert('Error reading file');
                //console.error(err);
                return;
            }
        }

        sendAjax(dataToSend);

    });

    $('#user-input').keypress(function(e) {
        if (e.which == 13) { // Enter key pressed
            $('#send-btn').click(); // Trigger the button click
        }
    });

});
