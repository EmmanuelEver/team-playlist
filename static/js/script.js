    var socket = io.connect('http://' + document.domain + ':' + location.port + '/room');

    socket.on("connect", function() {
        socket.send(`new user ${username}`);
        socket.emit("new-user",{user : username})
    });

const youtube_key = "AIzaSyDHiJGzz1h_qNV5yDNw3ry1oMeKuIxsfsc"
var queue = []
var results_container = $(".search-results")[0]
var queue_container = $(".queue-container")[0]
var search_input = $(".search-input")[0]


socket.on("new-user", function(data){
  var users = ""
  data.forEach(function(user){
    var user = `
                    <div class="user-item">
                       <img src="../static/images/avatar/${user.avatar}.png">
                       <h6 class="user-item-name">${user.username}</h6>
                     </div>
               `
    users += user
  })
  $(userlist).html(users)
})


socket.on("get-queue", function(data){
  console.log(data)
  data.forEach(function(video){
    console.log(`video: ${video}`)
    queue.push(video)
    addToQueueDiv(video.id, video.video_id, video.video_title, video.channel, video.publishTime, video.thumbnail, video.added_by)
  })
  
})


socket.on("new-queue", function(data){
  console.log(player.getPlayerState())
  console.log(queue.length)
  if (queue.length == 0 && player.getPlayerState !== 1){
    queue.push(data)
    player.loadVideoById({videoId:data.video_id})
    console.log("no songs in queue")
  }
  else {
    console.log(data)
    queue.push(data)
    addToQueueDiv(data.video_id, data.video_title, data.channel, data.publishTime, data.thumbnail, data.added_by)
  }
})



$(results_container).on("click",".result-item", function(){
   var videoId = $(this).attr("data-videoId");
   var title = $(this).find(".result-item-title").html()
   var channel = $(this).find(".result-item-channel strong").html()
   var publishTime = $(this).find(".date-uploaded").html()
   var thumbnail = $(this).find(".result-item-thumb img").attr("src")

  /*add the clicked item to the queue with this function*/

   addToQueue(videoId,title,channel,publishTime,thumbnail, username)           
   $(results_container).addClass("hidden")
   $(search_input).val("")
})

  /*function for querying resources from the youtube api */
     
function search_music(elem){
  $(results_container).removeClass("hidden")
        fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&q=${$(elem).val()}&type=video&maxResults=10&key=${youtube_key}`)
        .then(function(response){
         response.json()
        .then(function(data){
          console.log(data)
          var results = ""
          data.items.forEach(function(item){
            console.log(item)
            var title = item.snippet.title
            var channel = item.snippet.channelTitle
            var publishTime = formatDate(item.snippet.publishTime)
            var thumbnail = item.snippet.thumbnails.medium.url
            var videoId = item.id.videoId
            results +=
                `
                <div class="result-item"data-videoId=${videoId}>
                    <div class="result-item-thumb">
                      <img src="${thumbnail}">
                    </div>
                     <div class="result-item-details">
                      <h3 class="result-item-title">${title}</h3>
                      <p class="result-item-channel"> by: <strong>${channel}</strong> <span class="date-uploaded">${publishTime}</span></p>
                    </div>
                  </div>
                  `           
            })
          console.log(results)
          $(results_container).html(results)
        })
        })          
}      

    /* a simple function to format date */

function formatDate(date){
    var monthNames = [ "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC" ]; 
    var newDate = date.split("T")[0].split("-")
    return `${monthNames[1]} ${newDate[2]} ${newDate[0]}`
}

    /*function to process the new item*/

function addToQueue(id,video_title,video_channel,video_publishTime,video_thumbnail, user){
    var video_obj = {
               video_id: id,
               video_title: video_title,
               video_channel: video_channel,
               video_publishTime: video_publishTime,
               video_thumbnail: video_thumbnail,
               added_by: user
              }
    socket.emit("new-queue-item", video_obj)
}             

   /* function to add the new item to the queue div*/

function addToQueueDiv(id, video_id, title, channel, publishTime, thumbnail, added_by){
   var queue_item = ` <div class="queue-item" data-id=${id}>
                              <div class="music-thumb">
                                <img src="${thumbnail}">
                              </div>
                              <div class="music-details">
                                <h3 class="music-title">${title}</h3>
                                <p class="result-item-channel"> by: <strong>${channel} </strong> <span class="date-uploaded">${publishTime}</span></p>
                                <p class="added-by">added by: ${added_by}</p>
                              </div> 
                            </div> 
                           `
   $(queue_container).append(queue_item)       
}