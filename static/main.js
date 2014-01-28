jQuery(document).ready(
    function ($) {

        var $cells = $('.lookup-table td');
        $cells.click(function() {
            var cell_class = $.grep(this.className.split(/\s+/), function(c) {
                return c.indexOf('cell-') === 0;
            })[0];
            var $popup = $('.lookup-table-popup.' + cell_class);

            $popup.dialog({
                resizable: false,
                show: 'blind',
                width: '725px',
                height: 'auto',
                position:  {my: 'left top', at: 'right top', of: this},
                open: function (event) {
                    $('a.media-ondemand', event.target).each(function () {
                        var $link = $(this);
                        var $media = $link.next();
                        $media.attr('src', $link.attr('href'));
                        $link.remove();
                        if ($media.prop('nodeName') === 'VIDEO') {
                            $media.mediaelementplayer({
                                enablePluginSmoothing: true,
                                pauseOtherPlayers: false,
                                flashName: 'flashmediaelement-cdn.swf',
                            });
                        }
                    });
                },
                close: function (event) {
                    $('video', event.target).each(function () {
                        this.pause();
                        this.player.setCurrentTime(0);
                    });
                },
            });
            
        });

    }
);
