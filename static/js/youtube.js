      // 2. This code loads the IFrame Player API code asynchronously.
      var tag = document.createElement('script');


      tag.src = "https://www.youtube.com/iframe_api";
      var firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

      // 3. This function creates an <iframe> (and YouTube player)
      //    after the API code downloads.
      var player;
      function onYouTubeIframeAPIReady() {
        player = new YT.Player('player', {
          height: '100%',
          width: '100%',
          videoId: '',
          playerVars: {
                        fs: 0,
                        enablejsapi: 1,
                        modestbranding: 1,
                      },
          events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
          }
        });
      }
      // 4. The API will call this function when the video player is ready.
      function onPlayerReady(event) {
        if (queue.length>0) {
            console.log("queue is not empty")
            player.cueVideoById({videoId:queue[0].video_id})
            $(".queue-item").first().remove()
            console.log($(".queue-item").first())
            event.target.playVideo();
        }
        else {
            console.log("queue is empty")
        }

      }

      // 5. The API calls this function when the player's state changes.
      //    The function indicates that when playing a video (state=1),
      //    the player should play for six seconds and then stop.
      function onPlayerStateChange(event) {
        if (event.data == YT.PlayerState.ENDED) {
             var finished_music = queue.shift()
             socket.emit("finished_music", finished_music)
             if (queue.length > 0){
                player.cueVideoById({videoId:queue[0].video_id})
                $(".queue-item").first().remove()
                console.log($(".queue-item").first())
                playVideo()  
             }
        }
      }


      function stopVideo() {
        player.stopVideo();
      }

      function playVideo(){
        player.playVideo();
      }

