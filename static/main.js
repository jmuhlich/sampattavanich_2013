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
                position:  {my: 'left', at: 'right', of: this},
                open: function (event, ui) {
                    $('a.media-ondemand', event.target).each(function (index) {
                        $link = $(this);
                        $media = $link.next();
                        $media.attr('src', $link.attr('href'));
                        $link.remove();
                        if ($media.prop('nodeName') == 'VIDEO') {
                            $media.mediaelementplayer();
                        }
                    });
                },
                close: function (event, ui) {
                    $('video', event.target).each(function (index) {
                        this.pause();
                    });
                },
            });
            
        });

    }
);
