function display_alert(type, message){
    $("#alert-container").html('<div class="alert alert-' + type + '">'
        + '<button href="#" class="close" data-dismiss="alert">×</button>'
        + message + '</div>')
}

function handle(event){
    var btn = $(event.target)
    if(btn.attr('data-subscripe-vendor') != undefined) {
        $.post($SCRIPT_ROOT + "/ajax_subscripe", 
            {vendor_id : btn.attr('data-subscripe-vendor')})
    }
    else if(btn.attr('data-unsubscripe-vendor') != undefined) {
        $.post($SCRIPT_ROOT + "/ajax_unsubscripe", 
            {vendor_id : btn.attr('data-unsubscripe-vendor')})
    }  
}

//change the password of current user
function change_password(event){
    var jqxhr = $.post($SCRIPT_ROOT + "/ajax_change_password", 
        $("#change_password_form").serialize(),
        function(data, textStatus){
            display_alert("success", "Your password has been changed.")
        });
        
    jqxhr.error(function(){
        display_alert("error", "Sorry, we could not change your password. Maybe your misspelled your old one or the new ones don't match.")
    })
}

//show read articles of group
function toggle_read_articles(event){
	var btn = $(event.target)
	articles_container_id = "." + btn.attr('data-articles-container')
	if($(articles_container_id).is(":visible")){
		$(articles_container_id).hide()
		btn.html('<i class="icon-caret-right"></i> Show Read Article')	
	}
	else {
		$(articles_container_id).show()
		btn.html('<i class="icon-caret-down"></i> Hide Read Articles')	
	}
}

//add a new user to the database
function add_user(event){
    var jqxhr = $.post($SCRIPT_ROOT + "/ajax_add_user", 
        $("#add_user_form").serialize(),
        function(data, textStatus){
            display_alert("success", "A new user was added to the service.")
        });
        
    jqxhr.error(function(){
        display_alert("error", "Sorry, we could not add the new user.")
    })
}

$(function(){
    $('body').on('click', '.btn', handle)
    
    $('body').on('click', '#submit_password', change_password)
    $('body').on('click', '#submit_user', add_user)
    
    $('body').on('click', '.toggle_read_articles', toggle_read_articles)
    
    //$('.subnav').scrollspy()
})
