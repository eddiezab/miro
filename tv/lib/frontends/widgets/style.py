# Miro - an RSS based video player application

# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011
# Participatory Culture Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# In addition, as a special exception, the copyright holders give
# permission to link the code of portions of this program with the OpenSSL
# library.
#
# You must obey the GNU General Public License in all respects for all of
# the code used other than OpenSSL. If you modify file(s) with this
# exception, you may extend this exception to your version of the file(s),
# but you are not obligated to do so. If you do not wish to do so, delete
# this exception statement from your version. If you delete this exception
# statement from all source files in the program, then also delete it here.

"""Constants that define the look-and-feel."""

import math
import logging
import os

from miro import app
from miro import displaytext
from miro import prefs
from miro import signals
from miro import util
from miro.gtcache import gettext as _
from miro.frontends.widgets import cellpack
from miro.frontends.widgets import imagepool
from miro.frontends.widgets import widgetutil
from miro.plat import resources
from miro.plat.frontends.widgets import use_custom_tablist_font
from miro.plat.frontends.widgets import widgetset
from miro.plat.frontends.widgets import file_navigator_name

PI = math.pi

def css_to_color(css_string):
    parts = (css_string[1:3], css_string[3:5], css_string[5:7])
    return tuple((int(value, 16) / 255.0) for value in parts)

def font_scale_from_osx_points(points):
    """Create a font scale so that it's points large on OS X.

    Assumptions (these should be true for OS X)
        - the default font size is 13pt
        - the DPI is 72ppi
    """
    return points / 13.0

AVAILABLE_COLOR = (38/255.0, 140/255.0, 250/255.0) # blue
UNPLAYED_COLOR = (0.31, 0.75, 0.12) # green
DOWNLOADING_COLOR = (0.90, 0.45, 0.08) # orange
WATCHED_COLOR = (0.33, 0.33, 0.33) # dark grey
EXPIRING_COLOR = (0.95, 0.82, 0.11) # yellow-ish
EXPIRING_TEXT_COLOR = css_to_color('#7b949d')

TAB_LIST_BACKGROUND_COLOR = (221/255.0, 227/255.0, 234/255.0)

ERROR_COLOR = (0.90, 0.0, 0.0)
BLINK_COLOR = css_to_color('#fffb83')

class LowerBox(widgetset.Background):
    def size_request(self, layout_manager):
        return (0, 63)

    def draw(self, context, layout_manager):
        gradient = widgetset.Gradient(0, 2, 0, context.height)
        gradient.set_start_color(css_to_color('#d4d4d4'))
        gradient.set_end_color(css_to_color('#a8a8a8'))
        context.rectangle(0, 2, context.width, context.height)
        context.gradient_fill(gradient)

        context.set_line_width(1)
        context.move_to(0, 0.5)
        context.line_to(context.width, 0.5)
        context.set_color(css_to_color('#585858'))
        context.stroke()
        context.move_to(0, 1.5)
        context.line_to(context.width, 1.5)
        context.set_color(css_to_color('#e6e6e6'))
        context.stroke()

    def is_opaque(self):
        return True

class TabRenderer(widgetset.CustomCellRenderer):
    MIN_WIDTH = 120
    MIN_ICON_WIDTH_TALL = 25
    MIN_ICON_WIDTH = 16
    MIN_HEIGHT = 28
    MIN_HEIGHT_TALL = 31
    TALL_FONT_SIZE = 1.0
    FONT_SIZE = 0.85
    SELECTED_FONT_COLOR = widgetutil.WHITE
    SELECTED_FONT_SHADOW = widgetutil.BLACK

    def get_size(self, style, layout_manager):
        if (not use_custom_tablist_font or
            (hasattr(self.data, 'tall') and self.data.tall)):
            min_height = self.MIN_HEIGHT_TALL
            font_scale = self.TALL_FONT_SIZE
        else:
            min_height = self.MIN_HEIGHT
            font_scale = self.FONT_SIZE
        return (self.MIN_WIDTH, max(min_height,
            layout_manager.font(font_scale).line_height()))

    def render(self, context, layout_manager, selected, hotspot, hover):
        layout_manager.set_text_color(context.style.text_color)
        bold = False
        if selected:
            bold = True
            if use_custom_tablist_font:
                layout_manager.set_text_color(self.SELECTED_FONT_COLOR)
                layout_manager.set_text_shadow(widgetutil.Shadow(
                        self.SELECTED_FONT_SHADOW, 0.5, (0, -1), 0))
        if not use_custom_tablist_font or getattr(self.data, 'tall', False):
            min_icon_width = self.MIN_ICON_WIDTH_TALL
            layout_manager.set_font(self.TALL_FONT_SIZE, bold=bold)
        else:
            min_icon_width = self.MIN_ICON_WIDTH
            layout_manager.set_font(self.FONT_SIZE, bold=bold)
        titlebox = layout_manager.textbox(self.data.name)
        hbox = cellpack.HBox(spacing=4)
        self.pack_leading_space(hbox)
        if selected and hasattr(self.data, 'active_icon'):
            icon = self.data.active_icon
        else:
            icon = self.data.icon
        alignment = cellpack.Alignment(icon, yalign=0.5, yscale=0.0,
                xalign=0.0, xscale=0.0, min_width=min_icon_width)
        hbox.pack(alignment)
        hbox.pack(cellpack.align_middle(cellpack.TruncatedTextLine(titlebox)), expand=True)
        layout_manager.set_font(0.77)
        layout_manager.set_text_color(widgetutil.WHITE)
        self.pack_bubbles(hbox, layout_manager)
        hbox.pack_space(2)
        alignment = cellpack.Alignment(hbox, yscale=0.0, yalign=0.5)
        if self.blink:
            renderer = cellpack.Background(alignment)
            renderer.set_callback(self.draw_blink_background)
        else:
            renderer = alignment
        renderer.render_layout(context)

    def pack_leading_space(self, hbox):
        pass

    def pack_bubbles(self, hbox, layout_manager):
        if self.updating_frame > -1:
            image_name = 'icon-updating-%s' % self.updating_frame
            updating_image = widgetutil.make_surface(image_name)
            alignment = cellpack.Alignment(updating_image, yalign=0.5, yscale=0.0,
                    xalign=0.0, xscale=0.0, min_width=20)
            hbox.pack(alignment)
        else:
            if self.data.unwatched > 0:
                self.pack_bubble(hbox, layout_manager, self.data.unwatched,
                        UNPLAYED_COLOR)
            if self.data.available > 0:
                self.pack_bubble(hbox, layout_manager, self.data.available,
                        AVAILABLE_COLOR)

    def pack_bubble(self, hbox, layout_manager, count, color):
        radius = (layout_manager.current_font.line_height() + 2) / 2.0
        background = cellpack.Background(layout_manager.textbox(str(count)),
                margin=(1, radius, 1, radius))
        background.set_callback(self.draw_bubble, color)
        hbox.pack(cellpack.align_middle(background))

    def draw_bubble(self, context, x, y, width, height, color):
        radius = height / 2.0
        inner_width = width - radius * 2
        mid = y + radius

        context.move_to(x + radius, y)
        context.rel_line_to(inner_width, 0)
        context.arc(x + width - radius, mid, radius, -PI/2, PI/2)
        context.rel_line_to(-inner_width, 0)
        context.arc(x + radius, mid, radius, PI/2, -PI/2)
        context.set_color(color)
        context.fill()

    def draw_blink_background(self, context, x, y, width, height):
        context.rectangle(x, y, width, height)
        context.set_color(BLINK_COLOR)
        context.fill()

class StaticTabRenderer(TabRenderer):
    def pack_bubbles(self, hbox, layout_manager):
        if self.data.unwatched > 0:
            self.pack_bubble(hbox, layout_manager, self.data.unwatched,
                    UNPLAYED_COLOR)
        if self.data.downloading > 0:
            self.pack_bubble(hbox, layout_manager, self.data.downloading,
                    DOWNLOADING_COLOR)

class ConnectTabRenderer(TabRenderer):
    def pack_bubbles(self, hbox, layout_manager):
        if getattr(self.data, 'fake', False):
            return
        self.hbox = None
        if self.updating_frame > -1:
            return TabRenderer.pack_bubbles(self, hbox, layout_manager)
        if getattr(self.data, 'mount', None):
            eject_image = widgetutil.make_surface('icon-eject')
            hotspot = cellpack.Hotspot('eject-device', eject_image)
            alignment = cellpack.Alignment(hotspot, yalign=0.5, yscale=0.0,
                                           xalign=0.0, xscale=0.0, min_width=20)
            hbox.pack(alignment)
            self.hbox = hbox

    def hotspot_test(self, style, layout_manager, x, y, width, height):
        if self.hbox is None:
            return None
        hotspot_info = self.hbox.find_hotspot(x, y, width, height)
        if hotspot_info is None:
            return None
        else:
            return hotspot_info[0]

class FakeDownloadInfo(object):
    # Fake download info object used to size items
    def __init__(self):
        self.state = 'paused'
        self.rate = 0
        self.downloaded_size = 0

class ItemRendererSignals(signals.SignalEmitter):
    """Signal emitter for ItemRenderer.

    We could make ItemRenderer subclass SignalEmitter, but since it comes from
    widgetset that seems awkward.  Instead, this class handles the signals and
    it's set as a property of ItemRenderer

    signals:
        throbber-drawn (obj, item_info) -- a progress throbber was drawn
    """
    def __init__(self):
        signals.SignalEmitter.__init__(self, 'throbber-drawn')

class ItemRenderer(widgetset.InfoListRenderer):
    # dimensions
    MIN_WIDTH = 600
    HEIGHT = 147
    RIGHT_WIDTH = 90
    RIGHT_WIDTH_DOWNLOAD_MODE = 115
    IMAGE_WIDTH = 180
    CORNER_RADIUS = 5
    EMBLEM_HEIGHT = 20
    PROGRESS_AREA_HEIGHT = 56

    # padding/spacing
    PADDING = (15, 15, 5, 5)
    PADDING_BACKGROUND = (5, 5, 6, 6)
    TEXT_SPACING_Y = 3
    EMBLEM_PAD_TOP = 25
    EMBLEM_TEXT_PAD_START = 4
    EMBLEM_TEXT_PAD_END = 20
    EMBLEM_TEXT_PAD_END_SMALL = 6
    EMBLEM_MARGIN_RIGHT = 12

    # colors
    GRADIENT_TOP = css_to_color('#ffffff')
    GRADIENT_BOTTOM = css_to_color('#dfdfdf')
    THUMBNAIL_SEPARATOR_COLOR = widgetutil.BLACK
    INFO_SEPARATOR_COLOR = css_to_color('#aaaaaa')
    ITEM_TITLE_COLOR = widgetutil.BLACK
    DOWNLOAD_INFO_COLOR = widgetutil.WHITE
    DOWNLOAD_INFO_COLOR_UNEM = (0.2, 0.2, 0.2)
    DOWNLOAD_INFO_SEPARATOR_COLOR = widgetutil.WHITE
    DOWNLOAD_INFO_SEPARATOR_ALPHA = 0.1
    TORRENT_INFO_LABEL_COLOR = (0.6, 0.6, 0.6)
    TORRENT_INFO_DATA_COLOR = widgetutil.WHITE
    ITEM_DESC_COLOR = (0.3, 0.3, 0.3)
    FEED_NAME_COLOR = (0.5, 0.5, 0.5)
    PLAYLIST_ORDER_COLOR = widgetutil.BLACK
    RESUME_TEXT_COLOR = css_to_color('#306219')
    RESUME_TEXT_SHADOW = widgetutil.WHITE
    UNPLAYED_TEXT_COLOR = css_to_color('#d8ffc7')
    UNPLAYED_TEXT_SHADOW = widgetutil.BLACK
    EXPIRING_TEXT_COLOR = css_to_color('#6f6c28')
    EXPIRING_TEXT_SHADOW = widgetutil.WHITE
    NEWLY_AVAILABLE_TEXT_COLOR =  css_to_color('#e1efff')
    NEWLY_AVAILABLE_TEXT_SHADOW = widgetutil.BLACK
    DRM_TEXT_COLOR = css_to_color('#582016')
    DRM_TEXT_SHADOW = widgetutil.WHITE
    QUEUED_TEXT_COLOR = css_to_color('#4a2c00')
    QUEUED_TEXT_SHADOW = widgetutil.WHITE
    FAILED_TEXT_COLOR = css_to_color('#ffe7e7')
    FAILED_TEXT_SHADOW = widgetutil.BLACK

    # font sizes
    EMBLEM_FONT_SIZE = font_scale_from_osx_points(10)
    TITLE_FONT_SIZE = font_scale_from_osx_points(14)
    EXTRA_INFO_FONT_SIZE = font_scale_from_osx_points(10)
    ITEM_DESC_FONT_SIZE = font_scale_from_osx_points(11)
    DOWNLOAD_INFO_FONT_SIZE = 0.70
    DOWNLOAD_INFO_TORRENT_DETAILS_FONT_SIZE = 0.50

    # Emblem shadow settings
    EMBLEM_SHADOW_OPACITY = 0.6
    EMBLEM_SHADOW_OFFSET = (0, 1)
    EMBLEM_SHADOW_BLUR_RADIUS = 0

    # text assets
    REVEAL_IN_TEXT = (file_navigator_name and
            _("Reveal in %(progname)s", {"progname": file_navigator_name}) or _("Reveal File"))
    SHOW_CONTENTS_TEXT = _("display contents")
    WEB_PAGE_TEXT = _("Web Page")
    FILE_URL_TEXT = _("File URL")
    LICENSE_PAGE_TEXT = _("License Page")
    FILE_TYPE_TEXT = _("File Type")
    SEEDERS_TEXT = _("Seeders")
    LEECHERS_TEXT = _("Leechers")
    UPLOAD_RATE_TEXT = _("Upload Rate")
    UPLOAD_TOTAL_TEXT = _("Upload Total")
    DOWN_RATE_TEXT = _("Down Rate")
    DOWN_TOTAL_TEXT = _("Down Total")
    UP_DOWN_RATIO_TEXT = _("Up/Down Ratio")
    DOWNLOAD_TEXT = _("Download")
    DOWNLOAD_TO_MY_MIRO_TEXT = _("Download to My Miro")
    DOWNLOAD_TORRENT_TEXT = _("Download Torrent")
    ERROR_TEXT = _("Error")
    CANCEL_TEXT = _("Cancel")
    QUEUED_TEXT = _("Queued for Auto-download")
    UNPLAYED_TEXT = _("Unplayed")
    CURRENTLY_PLAYING_TEXT = _("Currently Playing")
    NEWLY_AVAILABLE_TEXT = _("Newly Available")
    KEEP_TEXT = _("Keep")
    SAVED_TEXT = _("Saved")
    REMOVE_TEXT = _("Remove")
    STOP_SEEDING_TEXT = _("Stop seeding")
    PLAYLIST_REMOVE_TEXT = _('Remove from playlist')

    def __init__(self, display_channel=True, is_podcast=False):
        widgetset.InfoListRenderer.__init__(self)
        self.signals = ItemRendererSignals()
        self.display_channel = display_channel
        self.is_podcast = is_podcast
        self.selected = False
        self.setup_images()
        self.emblem_drawer = _EmblemDrawer(self)
        self.extra_info_drawer = _ExtraInfoDrawer()
        self.setup_torrent_folder_description()

    def setup_torrent_folder_description(self):
        text = (u'<a href="#show-torrent-contents">%s</a>' %
                self.SHOW_CONTENTS_TEXT)
        self.torrent_folder_description = util.HTMLStripper().strip(text)

    def setup_images(self):
        all_images = [ 'background-left', 'background-middle',
                'background-right', 'dl-speed', 'dl-stats-left-cap',
                'dl-stats-middle', 'dl-stats-right-cap',
                'dl-stats-selected-left-cap', 'dl-stats-selected-middle',
                'dl-stats-selected-right-cap', 'download-pause',
                'download-pause-pressed', 'download-resume',
                'download-resume-pressed', 'download-stop',
                'download-stop-pressed', 'drm-middle', 'drm-cap',
                'expiring-cap', 'expiring-middle', 'failed-middle',
                'failed-cap', 'keep', 'keep-pressed', 'menu', 'menu-pressed',
                'pause', 'pause-pressed', 'play', 'play-pressed', 'remove',
                'remove-playlist', 'remove-playlist-pressed',
                'remove-pressed', 'saved', 'status-icon-alert', 'newly-cap',
                'newly-middle', 'progress-left-cap', 'progress-middle',
                'progress-right-cap', 'progress-throbber-1-left',
                'progress-throbber-1-middle', 'progress-throbber-1-right',
                'progress-throbber-2-left', 'progress-throbber-2-middle',
                'progress-throbber-2-right', 'progress-throbber-3-left',
                'progress-throbber-3-middle', 'progress-throbber-3-right',
                'progress-throbber-4-left', 'progress-throbber-4-middle',
                'progress-throbber-4-right', 'progress-throbber-5-left',
                'progress-throbber-5-middle', 'progress-throbber-5-right',
                'progress-track', 'queued-middle', 'queued-cap', 'resume-cap',
                'resume-middle', 'selected-background-left',
                'selected-background-middle', 'selected-background-right',
                'time-left', 'ul-speed', 'unplayed-cap', 'unplayed-middle', ]
        self.images = {}
        for image_name in all_images:
            filename = 'item-renderer-%s.png' % image_name
            surface = imagepool.get_surface(resources.path(
                os.path.join('images', filename)))
            self.images[image_name] = surface
        # download-arrow is a shared icon.  It doesn't have the same prefix.
        self.images['download-arrow'] = imagepool.get_surface(
                resources.path('images/download-arrow.png'))
        # setup progress throbber stages
        self.progress_throbber_surfaces = []
        for i in xrange(5):
            left = self.images['progress-throbber-%d-left' % (i + 1)]
            middle = self.images['progress-throbber-%d-middle' % (i + 1)]
            right = self.images['progress-throbber-%d-right' % (i + 1)]
            surface = widgetutil.ThreeImageSurface()
            surface.set_images(left, middle, right)
            self.progress_throbber_surfaces.append(surface)

    def get_size(self, style, layout_manager):
        return self.MIN_WIDTH, self.HEIGHT

    def calc_download_mode(self):
        self.download_mode = (self.info.state in ('downloading', 'paused'))
        # If the download has started and we don't know the total size.  Draw
        # a progress throbber.
        if self.download_mode:
            dl_info = self.info.download_info
            self.throbber_mode = (dl_info.downloaded_size > 0 and
                    dl_info.total_size < 0)

    def hotspot_test(self, style, layout_manager, x, y, width, height):
        self.download_info = self.info.download_info
        self.calc_download_mode()
        self.hotspot = None
        self.selected = False
        # Assume the mouse is over the cell, since we got a mouse click
        self.hover = True
        layout = self.layout_all(layout_manager, width, height)
        hotspot_info = layout.find_hotspot(x, y)
        self.extra_info_drawer.reset()
        if hotspot_info is None:
            return None
        hotspot, x, y = hotspot_info
        if hotspot == 'description':
            textbox = self.make_description(layout_manager)
            textbox.set_width(self.description_width)
            index = textbox.char_at(x, y)
            if index is None:
                return None
            index -= self.description_text_start
            if index < 0:
                return None
            for (start, end, url) in self.description_links:
                if start <= index < end:
                    if url == '#show-torrent-contents':
                        # special link that we set up in
                        # setup_torrent_folder_description()
                        return 'show_contents'
                    else:
                        return 'description-link:%s' % url
            return None
        else:
            return hotspot

    def render(self, context, layout_manager, selected, hotspot, hover):
        self.download_info = self.info.download_info
        self.calc_download_mode()
        self.hotspot = hotspot
        self.selected = selected
        self.hover = hover
        layout = self.layout_all(layout_manager, context.width,
                context.height)
        layout.draw(context)
        self.extra_info_drawer.reset()

    def layout_all(self, layout_manager, width, height):
        self.setup_guides(width, height)
        layout = cellpack.Layout()
        self.layout_simple_elements(layout, layout_manager)
        self.layout_text(layout, layout_manager)
        if self.download_mode:
            self.layout_progress_bar(layout, layout_manager)
            self.layout_download_right(layout, layout_manager)
        else:
            self.layout_main_bottom(layout, layout_manager)
            self.layout_right(layout, layout_manager)
        return layout

    def setup_guides(self, width, height):
        """Setup a few dimensions to help us layout the cell:

        This method sets the following attributes:
            background_rect - area where the background image should be drawn
            image_rect - area for the thumbnail
            middle_rect - area for the text/badges
            right_rect - area for the buttons/download information
        """
        total_rect = cellpack.LayoutRect(0, 0, width, height)
        # NOTE: background image extends a few pixels beyond the actual
        # boundaries so that it can draw shadows and other things
        self.background_rect = total_rect.subsection(*self.PADDING)
        # area inside the boundaries of the background
        inner_rect = self.background_rect.subsection(*self.PADDING_BACKGROUND)
        self.image_rect = inner_rect.left_side(self.IMAGE_WIDTH)
        if self.download_mode:
            right_width = self.RIGHT_WIDTH_DOWNLOAD_MODE
        else:
            right_width = self.RIGHT_WIDTH
        self.right_rect = inner_rect.right_side(right_width)
        self.middle_rect = inner_rect.subsection(self.IMAGE_WIDTH + 20,
                right_width + 15, 0 ,0)
        # emblem/progress bar should start 29px above the top of the cell
        self.emblem_bottom = total_rect.bottom - 29

    def layout_simple_elements(self, layout, layout_manager):
        # this is a place to put layout calls that are simple enough that they
        # don't need their own function
        layout.add_rect(self.background_rect, self.draw_background)
        layout.add_rect(self.image_rect, self.draw_thumbnail,
                self.calc_thumbnail_hotspot())
        layout.add_rect(self.image_rect.past_right(1),
                self.draw_thumbnail_separator)

    def calc_thumbnail_hotspot(self):
        """Decide what hotspot clicking on the thumbnail should activate."""
        if not self.info.downloaded:
            return 'thumbnail-download'
        elif self.info.is_playable:
            return 'thumbnail-play'
        else:
            return None

    def layout_text(self, layout, layout_manager):
        """layout the text for our cell """
        # setup title
        layout_manager.set_font(self.TITLE_FONT_SIZE,
                family=widgetset.ITEM_TITLE_FONT, bold=True)
        layout_manager.set_text_color(self.ITEM_TITLE_COLOR)
        title = layout_manager.textbox(self.info.name)
        title.set_wrap_style('truncated-char')
        # setup info lin
        layout_manager.set_font(self.EXTRA_INFO_FONT_SIZE,
                family=widgetset.ITEM_INFO_FONT)
        layout_manager.set_text_color(self.ITEM_DESC_COLOR)
        self.extra_info_drawer.setup(self.info, layout_manager,
            self.INFO_SEPARATOR_COLOR)
        # setup description
        description = self.make_description(layout_manager)

        # position the parts.

        total_height = (title.font.line_height() +
                + self.extra_info_drawer.height +
                description.font.line_height() + 16)
        x = self.middle_rect.x
        width = self.middle_rect.width
        # Ideally, we want to start it at 28px from the start of the top of
        # the cell.  However, if our text is big enough, don't let it overflow
        # the play button.
        text_bottom = min(28 + total_height, self.middle_rect.y + 80)
        self.text_top = text_bottom - total_height
        if self.download_mode:
            # quick interlude.  If we are in download mode, draw the menu on
            # the right side of the title line.
            menu_x = x + width - self.images['menu'].width
            self._add_image_button(layout, menu_x, self.text_top, 'menu',
                    '#show-context-menu')
            title_width = width - self.images['menu'].width - 5
        else:
            title_width = width

        layout.add_text_line(title, x, self.text_top, title_width)
        y = layout.last_rect.bottom + 8
        layout.add(x, y, width, self.extra_info_drawer.height,
            self.extra_info_drawer.draw)
        y = layout.last_rect.bottom + 8
        layout.add_text_line(description, x, y, width, hotspot='description')
        self.description_width = width

    def make_extra_info(self, layout_manager):
        layout_manager.set_font(self.DOWNLOAD_INFO_FONT_SIZE,
                family=widgetset.ITEM_DESC_FONT)
        layout_manager.set_text_color(self.ITEM_DESC_COLOR)
        parts = []
        for attr in (self.info.display_date, self.info.display_duration,
                self.info.display_size, self.info.file_format):
            if attr:
                parts.append(attr)
        return layout_manager.textbox(' | '.join(parts))

    def make_description(self, layout_manager):
        layout_manager.set_font(self.ITEM_DESC_FONT_SIZE,
                family=widgetset.ITEM_DESC_FONT)
        layout_manager.set_text_color(self.ITEM_DESC_COLOR)
        textbox = layout_manager.textbox("")
        self.description_text_start = self.add_description_preface(textbox)

        if (self.info.download_info and self.info.download_info.torrent and
                self.info.children):
            text, links = self.torrent_folder_description
        else:
            text, links = self.info.description_stripped

        pos = 0
        for start, end, url in links:
            textbox.append_text(text[pos:start])
            textbox.append_text(text[start:end], underline=True, color=self.ITEM_DESC_COLOR)
            pos = end
        if pos < len(text):
            textbox.append_text(text[pos:])
        self.description_links = links
        return textbox

    def add_description_preface(self, textbox):
        if self.display_channel and self.info.feed_name:
            feed_preface = "%s: " % self.info.feed_name
            textbox.append_text(feed_preface, color=self.FEED_NAME_COLOR)
            return len(feed_preface)
        else:
            return 0

    def layout_main_bottom(self, layout, layout_manager):
        """Layout the bottom part of the main section.

        rect should contain the area for the entire middle section.  This
        method will add the progress bar, emblem and/or play button.
        """

        # allocate it enough size to fit the play button
        self.emblem_drawer.info = self.info
        self.emblem_drawer.hotspot = self.hotspot
        emblem_width = self.emblem_drawer.add_to_layout(layout,
                layout_manager, self.middle_rect, self.emblem_bottom)
        # add stop seeding and similar buttons
        extra_button_x = (self.middle_rect.x + emblem_width +
                self.EMBLEM_MARGIN_RIGHT)
        self.add_extra_button(layout, layout_manager, extra_button_x)

    def add_extra_button(self, layout, layout_manager, left):
        button_info = self.calc_extra_button()
        if button_info is None:
            return
        else:
            text, hotspot = button_info
        layout_manager.set_font(self.EMBLEM_FONT_SIZE)
        button = layout_manager.button(text, pressed=(self.hotspot==hotspot),
                    style='webby')
        button_height = button.get_size()[1]
        y = (self.emblem_bottom - (self.EMBLEM_HEIGHT - button_height) // 2 -
                button_height)
        layout.add_image(button, left, y, hotspot)

    def calc_extra_button(self):
        """Calculate the button to put to the right of the emblem.

        :returns: (text, hotspot_name) tuple, or None
        """
        if (self.info.download_info and
                self.info.download_info.state == 'uploading'):
            return (self.STOP_SEEDING_TEXT, 'stop_seeding')
        elif self.info.pending_auto_dl:
            return (self.CANCEL_TEXT, 'cancel_auto_download')
        return None

    def layout_right(self, layout, layout_manager):
        button_width, button_height = self.images['keep'].get_size()
        x = self.right_rect.right - button_width - 20
        # align the buttons based on where other parts get laid out.
        top = self.text_top - 1
        bottom = self.emblem_bottom

        # top botton is easy
        menu_y = top
        expire_y = bottom - button_height
        delete_y = ((top + bottom - button_height) // 2)

        self._add_image_button(layout, x, menu_y, 'menu',
                '#show-context-menu')

        if ((self.info.is_external or self.info.downloaded) and 
            self.info.source_type != 'sharing'):
            self.add_remove_button(layout, x, delete_y)

        if self.info.expiration_date:
            expire_rect = cellpack.LayoutRect(x, expire_y, button_width,
                    button_height)
            text = displaytext.expiration_date(self.info.expiration_date)
            image = self._make_image_button('keep', 'keep')
            hotspot = 'keep'
            self.layout_expire(layout, layout_manager, expire_rect, text,
                    image, hotspot)
            self.expire_background_alpha = 1.0
        elif self.attrs.get('keep-animation-alpha', 0) > 0:
            expire_rect = cellpack.LayoutRect(x, expire_y, button_width,
                    button_height)
            text = self.SAVED_TEXT
            image = self.images['saved']
            hotspot = None
            self.layout_expire(layout, layout_manager, expire_rect, text,
                    image, hotspot)
            self.expire_background_alpha = self.attrs['keep-animation-alpha']

    def add_remove_button(self, layout, x, y):
        """Add the remove button to a layout.
        
        Subclasses can override this if they want different behavior/looks for
        the button.
        """
        self._add_image_button(layout, x, y, 'remove', 'delete')

    def layout_expire(self, layout, layout_manager, rect, text, image, hotspot):
        # create a new Layout for the 2 elements
        expire_layout = cellpack.Layout()
        # add the background now so that it's underneath everything else.  We
        # don't know anything about the x dimensions yet, so just set them to
        # 0
        background_rect = expire_layout.add(0, 0, 0, self.EMBLEM_HEIGHT,
                self.draw_expire_background)
        # create text for the emblem
        layout_manager.set_font(self.EMBLEM_FONT_SIZE)
        layout_manager.set_text_color(self.EXPIRING_TEXT_COLOR)
        textbox = layout_manager.textbox(text)
        # add text.  completely break the bounds of our layout rect and
        # position the text to the left of our rect
        text_width, text_height = textbox.get_size()
        text_x = rect.x - self.EMBLEM_TEXT_PAD_START - text_width
        expire_layout.add(text_x, 0, text_width, text_height, textbox.draw)
        # add button
        button_rect = expire_layout.add_image(image, rect.x, 0, hotspot)
        # now we can position the background, draw it to the middle of the
        # button.
        background_rect.x = text_x - self.EMBLEM_TEXT_PAD_END
        background_rect.width = (rect.x - background_rect.x +
                button_rect.width // 2)
        # middle align everything and add it to layout
        expire_layout.center_y(top=rect.y, bottom=rect.bottom)
        layout.merge(expire_layout)

    def layout_progress_bar(self, layout, layout_manager):
        left = self.middle_rect.x
        width = self.middle_rect.width
        top = self.emblem_bottom - self.images['progress-track'].height
        height = 22
        end_button_width = 47
        progress_cap_width = 10
        if self.throbber_mode:
            # ensure that the progress bar width is divisible by 10.  That
            # makes the progress throbber animations line up
            button_width_extra = end_button_width * 2 - progress_cap_width * 2
            width -= (width - button_width_extra) % 10
        # figure out what button goes on the left
        if not self.download_info or self.download_info.state != 'paused':
            left_hotspot = 'pause'
            left_button_name = 'download-pause'
        else:
            left_hotspot = 'resume'
            left_button_name = 'download-resume'

        # add ends of the bar
        self._add_image_button(layout, left, top, left_button_name,
                left_hotspot)
        right_button_x = left + width - end_button_width
        self._add_image_button(layout, right_button_x, top, 'download-stop',
                'cancel')
        # add track in the middle
        track = self.images['progress-track']
        track_x = left + end_button_width
        track_rect = cellpack.LayoutRect(track_x, top, right_button_x - track_x,
                height)
        layout.add_rect(track_rect, track.draw)

        # add progress bar above the track
        progress_x = track_x - progress_cap_width
        bar_width_total = (right_button_x - progress_x) + progress_cap_width
        bar_rect = cellpack.LayoutRect(progress_x, top, bar_width_total, height)
        layout.add_rect(bar_rect, self.draw_progress_bar)

    def layout_download_right(self, layout, layout_manager):
        dl_info = self.info.download_info
        # add some padding around the edges
        content_rect = self.right_rect.subsection(6, 12, 8, 8)
        x = content_rect.x
        width = content_rect.width

        # layout top
        layout_manager.set_font(self.DOWNLOAD_INFO_FONT_SIZE)
        line_height = layout_manager.current_font.line_height()
        ascent = layout_manager.current_font.ascent()
        # generic code to layout a line at the top
        def add_line(y, image_name, text, subtext=None):
            # position image so that it's bottom is the baseline for the text
            image = self.images[image_name]
            image_y = y + ascent - image.height + 3
            # add 3 px to account for the shadow at the bottom of the icons
            layout.add_image(image, x, image_y)
            if text:
                layout_manager.set_text_color(self.DOWNLOAD_INFO_COLOR)
                textbox = layout_manager.textbox(text)
                textbox.set_alignment('right')
                layout.add_text_line(textbox, x, y, width)
            if subtext:
                layout_manager.set_text_color(self.DOWNLOAD_INFO_COLOR_UNEM)
                subtextbox = layout_manager.textbox(subtext)
                subtextbox.set_alignment('right')
                layout.add_text_line(subtextbox, x, y + line_height, width)
        if self.info.state == 'paused':
            eta = rate = 0
        else:
            eta = dl_info.eta
            rate = dl_info.rate

        # layout line 1
        current_y = self.right_rect.y + 10
        add_line(current_y, 'time-left', displaytext.time_string_0_blank(eta))
        current_y += max(19, line_height)
        layout.add(x, current_y-1, width, 1,
                self.draw_download_info_separator)
        # layout line 2
        add_line(current_y, 'dl-speed',
                displaytext.download_rate(rate),
                displaytext.size_string(dl_info.downloaded_size))
        current_y += max(25, line_height * 2)
        layout.add(x, current_y-1, width, 1,
                self.draw_download_info_separator)
        # layout line 3
        if dl_info.torrent:
            add_line(current_y, 'ul-speed',
                    displaytext.download_rate(self.info.up_rate),
                    displaytext.size_string(self.info.up_total))
        current_y += max(25, line_height * 2)
        layout.add(x, current_y-1, width, 1,
                self.draw_download_info_separator)
        # layout torrent info
        if dl_info.torrent and dl_info.state != 'paused':
            torrent_info_height = content_rect.bottom - current_y
            self.layout_download_right_torrent(layout, layout_manager,
                    content_rect.bottom_side(torrent_info_height))

    def layout_download_right_torrent(self, layout, layout_manager, rect):
        if self.info.download_info.rate == 0:
            # not started yet, just display the startup activity
            layout_manager.set_text_color(self.TORRENT_INFO_DATA_COLOR)
            textbox = layout_manager.textbox(
                    self.info.download_info.startup_activity)
            height = textbox.get_size()[1]
            y = rect.bottom - height # bottom-align the textbox.
            layout.add(rect.x, y, rect.width, height,
                    textbox.draw)
            return

        layout_manager.set_font(self.DOWNLOAD_INFO_TORRENT_DETAILS_FONT_SIZE,
                family=widgetset.ITEM_DESC_FONT)
        lines = (
                (_('PEERS'), str(self.info.connections)),
                (_('SEEDS'), str(self.info.seeders)),
                (_('LEECH'), str(self.info.leechers)),
                (_('SHARE'), "%.2f" % self.info.up_down_ratio),
        )
        line_height = layout_manager.current_font.line_height()
        # check that we're not drawing more lines that we have space for.  If
        # there are extras, cut them off from the bottom
        potential_lines = int(rect.height // line_height)
        lines = lines[:potential_lines]
        total_height = line_height * len(lines)
        y = rect.bottom - total_height

        for label, value in lines:
            layout_manager.set_text_color(self.TORRENT_INFO_LABEL_COLOR)
            labelbox = layout_manager.textbox(label)
            layout_manager.set_text_color(self.TORRENT_INFO_DATA_COLOR)
            databox = layout_manager.textbox(value)
            databox.set_alignment('right')
            layout.add_text_line(labelbox, rect.x, y, rect.width)
            layout.add_text_line(databox, rect.x, y, rect.width)
            y += line_height

    def _make_image_button(self, image_name, hotspot_name):
        if self.hotspot != hotspot_name:
            return self.images[image_name]
        else:
            return self.images[image_name + '-pressed']

    def _add_image_button(self, layout, x, y, image_name, hotspot_name):
        image = self._make_image_button(image_name, hotspot_name)
        return layout.add_image(image, x, y, hotspot=hotspot_name)

    def draw_background(self, context, x, y, width, height):
        if self.selected:
            left = self.images['selected-background-left']
            thumb = self.images['dl-stats-selected-middle']
            middle = self.images['selected-background-middle']
            right = self.images['selected-background-right']
        else:
            left = self.images['background-left']
            thumb = self.images['dl-stats-middle']
            middle = self.images['background-middle']
            right = self.images['background-right']


        # draw left
        left.draw(context, x, y, left.width, height)
        # draw right
        if self.download_mode:
            right_width = self.RIGHT_WIDTH_DOWNLOAD_MODE
            download_info_x = x + width - right_width
            self.draw_download_info_background(context, download_info_x, y,
                    right_width)
        else:
            right_width = right.width
            right.draw(context, x + width - right_width, y, right_width,
                    height)
        image_end_x = self.image_rect.right
        # draw middle
        middle_end_x = x + width - right_width
        middle_width = middle_end_x - image_end_x
        middle.draw(context, image_end_x, y, middle_width, height)

        # draw thumbnail background
        thumbnail_background_width = image_end_x - (x + left.width)
        thumb.draw(context, x + left.width, y, thumbnail_background_width,
                height)

    def draw_download_info_background(self, context, x, y, width):
        if self.selected:
            left = self.images['dl-stats-selected-left-cap']
            middle = self.images['dl-stats-selected-middle']
            right = self.images['dl-stats-selected-right-cap']
        else:
            left = self.images['dl-stats-left-cap']
            middle = self.images['dl-stats-middle']
            right = self.images['dl-stats-right-cap']
        background = widgetutil.ThreeImageSurface()
        background.set_images(left, middle, right)
        background.draw(context, x, y, width)

    def draw_download_info_separator(self, context, x, y, width, height):
        context.set_color(self.DOWNLOAD_INFO_SEPARATOR_COLOR,
                self.DOWNLOAD_INFO_SEPARATOR_ALPHA)
        context.rectangle(x, y, width, height)
        context.fill()

    def draw_thumbnail(self, context, x, y, width, height):
        icon = imagepool.get_surface(self.info.thumbnail, (width, height))
        icon_x = x + (width - icon.width) // 2
        icon_y = y + (height - icon.height) // 2
        # if our thumbnail is far enough to the left, we need to set a clip
        # path to take off the left corners.
        make_clip_path = (icon_x < x + self.CORNER_RADIUS)
        if make_clip_path:
            # save context since we are setting a clip path
            context.save()
            # make a path with rounded edges on the left side and clip to it.
            radius = self.CORNER_RADIUS
            context.move_to(x + radius, y)
            context.line_to(x + width, y)
            context.line_to(x + width, y + height)
            context.line_to(x + radius, y + height)
            context.arc(x + radius, y + height - radius, radius, PI/2, PI)
            context.line_to(x, y + radius)
            context.arc(x + radius, y + radius, radius, PI, PI*3/2)
            context.clip()
        # draw the thumbnail
        icon.draw(context, icon_x, icon_y, icon.width, icon.height)
        if make_clip_path:
            # undo the clip path
            context.restore()

    def draw_thumbnail_separator(self, context, x, y, width, height):
        """Draw the separator just to the right of the thumbnail."""
        # width should be 1px, just fill in our entire space with our color
        context.rectangle(x, y, width, height)
        context.set_color(self.THUMBNAIL_SEPARATOR_COLOR)
        context.fill()

    def draw_expire_background(self, context, x, y, width, height):
        middle_image = self.images['expiring-middle']
        cap_image = self.images['expiring-cap']
        # draw the cap at the left
        cap_image.draw(context, x, y, cap_image.width, cap_image.height,
                fraction=self.expire_background_alpha)
        # repeat the middle to be as long as we need.
        middle_image.draw(context, x + cap_image.width, y,
                width - cap_image.width, middle_image.height,
                fraction=self.expire_background_alpha)

    def draw_progress_bar(self, context, x, y, width, height):
        if self.throbber_mode:
            self.draw_progress_throbber(context, x, y, width, height)
            return
        if self.info.size == 0:
            # We don't know the size yet, but we aren't sure that we won't in
            # a bit.  Probably we are starting up a download and haven't
            # gotten anything back from the server.  Don't draw the progress
            # bar or the throbber, just leave eerything blank.
            return
        progress_ratio = (float(self.info.download_info.downloaded_size) /
                self.info.size)
        progress_width = int(width * progress_ratio)
        left = self.images['progress-left-cap']
        middle = self.images['progress-middle']
        right = self.images['progress-right-cap']

        left_width = min(left.width, progress_width)
        right_width = max(0, progress_width - (width - right.width))
        middle_width = max(0, progress_width - left_width - right_width)

        left.draw(context, x, y, left_width, height)
        middle.draw(context, x + left.width, y, middle_width, height)
        right.draw(context, x + width - right.width, y, right_width, height)

    def draw_progress_throbber(self, context, x, y, width, height):
        throbber_count = self.attrs.get('throbber-value', 0)
        index = throbber_count % len(self.progress_throbber_surfaces)
        surface = self.progress_throbber_surfaces[index]
        surface.draw(context, x, y, width)
        self.signals.emit('throbber-drawn', self.info)

class _ExtraInfoDrawer(object):
    """Layout an draw the line below the item title."""
    def setup(self, info, layout_manager, separator_color):
        self.separator_color = separator_color
        self.textboxes = []
        for attr in (info.display_date, info.display_duration,
                info.display_size, info.file_format):
            if attr:
                self.textboxes.append(layout_manager.textbox(attr))
        self.height = layout_manager.current_font.line_height()

    def reset(self):
        self.textboxes = []

    def draw(self, context, x, y, width, height):
        for textbox in self.textboxes:
            text_width, text_height = textbox.get_size()
            textbox.draw(context, x, y, text_width, text_height)
            # draw separator
            separator_x = round(x + text_width + 4)
            context.set_color(self.separator_color)
            context.rectangle(separator_x, y, 1, height)
            context.fill()
            x += text_width + 8

class _EmblemDrawer(object):
    """Layout and draw emblems

    This is actually a fairly complex task, so the code is split out of
    ItemRenderer to make things more managable
    """

    def __init__(self, renderer):
        self.images = renderer.images
        self.is_podcast = renderer.is_podcast
        self.info = None
        self.hotspot = None
        # HACK: take all the style info from the renderer
        for name in dir(renderer):
            if name.isupper():
                setattr(self, name, getattr(renderer, name))

    def add_to_layout(self, layout, layout_manager, middle_rect, emblem_bottom):
        """Add emblem elements to a Layout()

        :param layout: Layout to add to
        :param layout_manager: LayoutManager to use
        :param middle_rect: middle area of the cell
        """

        x = middle_rect.x
        emblem_top = emblem_bottom  - self.EMBLEM_HEIGHT
        # make the button that appears to the left of the emblem
        button, button_hotspot = self.make_emblem_button(layout_manager)
        button_width, button_height = button.get_size()
        # make the button middle aligned along the emblem
        button_y = emblem_top - (button_height - self.EMBLEM_HEIGHT) // 2
        # figure out the text and/or image inside the emblem
        self._calc_emblem_parts()
        # check if we don't have anything to put inside our emblem.  Just draw
        # the button if so
        if self.image is None and self.text is None:
            layout.add_image(button, x, button_y, button_hotspot)
            return layout.last_rect.width
        # add emblem background first, since we want it drawn on the bottom.
        # We won't know the width until we lay out the text/images, so
        # set it to 0
        emblem_rect = layout.add(x + button_width // 2, emblem_top, 0,
                self.EMBLEM_HEIGHT, self.draw_emblem_background)
        # make a new Layout to vertically center the emblem images/text
        content_layout = cellpack.Layout()
        # Position it in the middle of the button, since we don't want it to
        # spill over on the left side.
        content_x = x + button_width + self.EMBLEM_TEXT_PAD_START
        content_width = self._add_text_images(content_layout, layout_manager,
                content_x)
        emblem_rect.right = (content_x + content_width + self.margin_right)
        content_layout.center_y(top=emblem_top, bottom=emblem_bottom)
        layout.merge(content_layout)
        # add button and we're done
        layout.add_image(button, x, button_y, button_hotspot)
        return emblem_rect.right - x

    def make_emblem_button(self, layout_manager):
        """Make the button that will go on the left of the emblem.

        :returns: a tuple contaning (button, hotspot_name)
        """
        layout = cellpack.Layout()

        layout_manager.set_font(0.85)
        if self.info.downloaded:
            if self.info.is_playable:
                playing_item = app.playback_manager.get_playing_item()
                if (playing_item and playing_item.id == self.info.id):
                    hotspot = 'play_pause'
                    if app.playback_manager.is_paused:
                        button_name = 'play'
                    else:
                        button_name = 'pause'
                else:
                    button_name = 'play'
                    hotspot = 'play'
                if self.hotspot == hotspot:
                    button_name += '-pressed'
                button = self.images[button_name]
            else:
                button = layout_manager.button(self.REVEAL_IN_TEXT,
                        pressed=(self.hotspot=='show_local_file'),
                        style='webby')
                hotspot = 'show_local_file'
        else:
            if self.info.mime_type == 'application/x-bittorrent':
                text = self.DOWNLOAD_TORRENT_TEXT
            else:
                text = self.DOWNLOAD_TEXT
            button = layout_manager.button(text,
                    pressed=(self.hotspot=='download'),
                    style='webby')
            button.set_icon(self.images['download-arrow'])
            hotspot = 'download'
        return button, hotspot

    def _calc_emblem_parts(self):
        """Calculate UI details for layout_emblem().

        This will set the following attributes, which we can then use to
        render stuff:
            text -- text inside the emblem
            text_bold -- should the text be bold?
            text_color -- color of text
            image -- image inside the emblem
            margin-right -- padding to add to the right of the text/image
            emblem -- name of the image to use to draw the backgound

        """

        self.text = self.image = None
        self.margin_right = self.EMBLEM_TEXT_PAD_END
        self.text_bold = False

        if self.info.has_drm:
            # FIXME need a new emblem for this
            self.text_bold = True
            self.text = _('DRM locked')
            self.text_color = self.DRM_TEXT_COLOR
            self.text_shadow = self.DRM_TEXT_SHADOW
            self.emblem = 'drm'
        elif (self.info.download_info
                and self.info.download_info.state == 'failed'):
            # FIXME need colors for this
            self.text_color = self.FAILED_TEXT_COLOR
            self.text_shadow = self.FAILED_TEXT_SHADOW
            self.text_bold = True
            self.image = self.images['status-icon-alert']
            self.text = u"%s-%s" % (self.ERROR_TEXT,
                    self.info.download_info.short_reason_failed)
            self.emblem = 'failed'
        elif self.info.pending_auto_dl:
            # FIXME need colors for this
            self.text_color = self.QUEUED_TEXT_COLOR
            self.text_shadow = self.QUEUED_TEXT_SHADOW
            self.text = self.QUEUED_TEXT
            self.emblem = 'queued'
        elif (self.info.downloaded
                and app.playback_manager.is_playing_id(self.info.id)):
            self.text = self.CURRENTLY_PLAYING_TEXT
            # copy the unplayed-style
            self.text_color = self.UNPLAYED_TEXT_COLOR
            self.text_shadow = self.UNPLAYED_TEXT_SHADOW
            self.emblem = 'unplayed'
        elif (self.info.downloaded and not self.info.video_watched and
                self.info.is_playable):
            self.text_color = self.UNPLAYED_TEXT_COLOR
            self.text_shadow = self.UNPLAYED_TEXT_SHADOW
            self.text_bold = True
            self.text = self.UNPLAYED_TEXT
            self.emblem = 'unplayed'
        elif self.should_resume_item():
            self.text_bold = True
            self.text_color = self.RESUME_TEXT_COLOR
            self.text_shadow = self.RESUME_TEXT_SHADOW
            self.text = _("Resume at %(resumetime)s",
                     {"resumetime": displaytext.short_time_string(self.info.resume_time)})
            self.margin_right = self.EMBLEM_TEXT_PAD_END_SMALL
            self.emblem = 'resume'
        elif not self.info.item_viewed and self.info.state == "new":
            self.text_bold = True
            self.text_color = self.NEWLY_AVAILABLE_TEXT_COLOR
            self.text_shadow = self.NEWLY_AVAILABLE_TEXT_SHADOW
            self.text = self.NEWLY_AVAILABLE_TEXT
            self.margin_right = self.EMBLEM_TEXT_PAD_END_SMALL
            self.emblem = 'newly'

    def should_resume_item(self):
        if self.is_podcast:
            resume_pref = prefs.RESUME_PODCASTS_MODE
        elif self.info.file_type == u'video':
            resume_pref = prefs.RESUME_VIDEOS_MODE
        else:
            resume_pref = prefs.RESUME_MUSIC_MODE
        return (self.info.is_playable
              and self.info.item_viewed
              and self.info.resume_time > 0
              and app.config.get(resume_pref))

    def _add_text_images(self, emblem_layout, layout_manager, left_x):
        """Add the emblem text and/or image

        :returns: the width used
        """
        x = left_x

        if self.image:
            emblem_layout.add_image(self.image, x, 0)
            x += self.image.width
        if self.text:
            layout_manager.set_font(self.EMBLEM_FONT_SIZE,
                    bold=self.text_bold)
            layout_manager.set_text_color(self.text_color)
            shadow = widgetutil.Shadow(self.text_shadow,
                    self.EMBLEM_SHADOW_OPACITY, self.EMBLEM_SHADOW_OFFSET,
                    self.EMBLEM_SHADOW_BLUR_RADIUS)
            layout_manager.set_text_shadow(shadow)
            textbox = layout_manager.textbox(self.text)
            text_width, text_height = textbox.get_size()
            emblem_layout.add(x, 0, text_width, text_height, textbox.draw)
            x += text_width
            layout_manager.set_text_shadow(None)
        return x - left_x

    def draw_emblem_background(self, context, x, y, width, height):
        middle_image = self.images[self.emblem + '-middle']
        cap_image = self.images[self.emblem + '-cap']
        # repeat the middle to be as long as we need.
        middle_image.draw(context, x, y, width - cap_image.width,
                middle_image.height)
        # draw the cap at the end
        cap_image.draw(context, x + width-cap_image.width, y, cap_image.width,
                cap_image.height)

class PlaylistItemRenderer(ItemRenderer):
    def __init__(self, playlist_sorter):
        ItemRenderer.__init__(self, display_channel=False)
        self.playlist_sorter = playlist_sorter

    def add_remove_button(self, layout, x, y):
        self._add_image_button(layout, x, y, 'remove-playlist', 'remove')

    def add_description_preface(self, textbox):
        order_number = self.playlist_sorter.sort_key(self.info) + 1
        if self.info.description_stripped[0]:
            sort_key_preface = "%s - " % order_number
        else:
            sort_key_preface = str(order_number)
        textbox.append_text(sort_key_preface, color=self.PLAYLIST_ORDER_COLOR)
        return len(sort_key_preface)

class SharingItemRenderer(ItemRenderer):
    def calc_extra_button(self):
        return self.DOWNLOAD_TO_MY_MIRO_TEXT, 'download-sharing-item'

class DeviceItemRenderer(ItemRenderer):
    DOWNLOAD_SHARING_ITEM_TEXT = _("Download to My Miro")

    def calc_extra_button(self):
        return self.DOWNLOAD_TO_MY_MIRO_TEXT, 'download-device-item'

# Renderers for the list view
class ListViewRendererText(widgetset.InfoListRendererText):
    """Renderer for list view columns that are just plain text"""

    bold = False
    color = (0.17, 0.17, 0.17)
    font_size = 0.82
    min_width = 50
    right_aligned = False

    def __init__(self):
        widgetset.InfoListRendererText.__init__(self)
        self.set_bold(self.bold)
        self.set_color(self.color)
        self.set_font_scale(self.font_size)
        if self.right_aligned:
            self.set_align('right')

    def get_value(self, info):
        return getattr(info, self.attr_name)

class DescriptionRenderer(ListViewRendererText):
    color = (0.6, 0.6, 0.6)
    attr_name = 'description_oneline'

class FeedNameRenderer(ListViewRendererText):
    attr_name = 'feed_name'

class DateRenderer(ListViewRendererText):
    attr_name = 'display_date'

class LengthRenderer(ListViewRendererText):
    attr_name = 'display_duration'

class ETARenderer(ListViewRendererText):
    right_aligned = True
    attr_name = 'display_eta'

class TorrentDetailsRenderer(ListViewRendererText):
    attr_name = 'display_torrent_details'

class DownloadRateRenderer(ListViewRendererText):
    right_aligned = True
    attr_name = 'display_rate'

class SizeRenderer(ListViewRendererText):
    right_aligned = True
    attr_name = 'display_size'

class ArtistRenderer(ListViewRendererText):
    attr_name = 'artist'

class AlbumRenderer(ListViewRendererText):
    attr_name = 'album'

class TrackRenderer(ListViewRendererText):
    attr_name = 'display_track'

class YearRenderer(ListViewRendererText):
    attr_name = 'display_year'

class GenreRenderer(ListViewRendererText):
    attr_name = 'genre'

class DateAddedRenderer(ListViewRendererText):
    attr_name = 'display_date_added'

class LastPlayedRenderer(ListViewRendererText):
    attr_name = 'display_last_played'

class DRMRenderer(ListViewRendererText):
    attr_name = 'display_drm'

class FileTypeRenderer(ListViewRendererText):
    attr_name = 'file_format'

class ShowRenderer(ListViewRendererText):
    attr_name = 'show'

class KindRenderer(ListViewRendererText):
    attr_name = 'display_kind'

class PlaylistOrderRenderer(ListViewRendererText):
    """Displays the order an item is in a particular playlist.
    """
    def __init__(self, playlist_sorter):
        ListViewRendererText.__init__(self)
        self.playlist_sorter = playlist_sorter

    def get_value(self, info):
        return str(self.playlist_sorter.sort_key(info))

class ListViewRenderer(widgetset.InfoListRenderer):
    """Renderer for more complex list view columns.

    This class is useful for renderers that use the cellpack.Layout class.
    """
    font_size = 0.82
    default_text_color = (0.17, 0.17, 0.17)
    min_width = 5
    min_height = 0

    def hotspot_test(self, style, layout_manager, x, y, width, height):
        layout = self.layout_all(layout_manager, width, height)
        hotspot_info = layout.find_hotspot(x, y)
        if hotspot_info is None:
            return None
        hotspot, x, y = hotspot_info
        return hotspot

    def get_size(self, style, layout_manager):
        layout_manager.set_font(self.font_size)
        height = max(self.min_height,
                layout_manager.current_font.line_height())
        return (self.min_width, height)

    def render(self, context, layout_manager, selected, hotspot, hover):
        layout = self.layout_all(layout_manager, context.width, context.height)
        layout.draw(context)

    def layout_all(self, layout_manager, width, height):
        """Layout the contents of this cell

        Subclasses must implement this method

        :param layout_manager: LayoutManager object
        :param width: width of the area to lay the cell out in
        :param height: height of the area to lay the cell out in
        :returns: cellpack.Layout object
        """
        raise NotImplementedError()


class NameRenderer(ListViewRenderer):
    min_width = 100
    button_font_size = 0.77

    def __init__(self):
        widgetset.InfoListRenderer.__init__(self)
        path = resources.path('images/download-arrow.png')
        self.download_icon = imagepool.get_surface(path)

    def layout_all(self, layout_manager, width, height):
        # make a Layout Object
        layout = cellpack.Layout()
        # add the button, if needed
        if self.should_show_download_button():
            button = self.make_button(layout_manager)
            button_x = width - button.get_size()[0]
            layout.add_image(button, button_x, 0, hotspot='download')
            # text should end at the start of the button
            text_width = button_x
        else:
            # text can take up the whole space
            text_width = width
        # add the text
        layout_manager.set_font(self.font_size)
        layout_manager.set_text_color(self.default_text_color)
        textbox = layout_manager.textbox(self.info.name)
        textbox.set_wrap_style('truncated-char')
        layout.add_text_line(textbox, 0, 0, text_width)
        # middle-align everything
        layout.center_y(top=0, bottom=height)
        return layout

    def make_button(self, layout_manager):
        layout_manager.set_font(self.button_font_size)
        button = layout_manager.button(_("Download"))
        button.set_icon(self.download_icon)
        return button

    def should_show_download_button(self):
        return (not self.info.downloaded and
                self.info.state not in ('downloading', 'paused'))

class StatusRenderer(ListViewRenderer):
    BUTTONS = ('pause', 'resume', 'cancel', 'keep')
    min_width = 40
    min_height = 20

    def __init__(self):
        ListViewRenderer.__init__(self)
        self.button = {}
        for button in self.BUTTONS:
            path = resources.path('images/%s-button.png' % button)
            self.button[button] = imagepool.get_surface(path)

    def layout_all(self, layout_manager, width, height):
        if (self.info.state in ('downloading', 'paused') and
            self.info.download_info.state != 'pending'):
            return self.layout_progress(layout_manager, width, height)
        else:
            return self.layout_text(layout_manager, width, height)

    def layout_progress(self, layout_manager, width, height):
        """Handle layout when we should display a progress bar """

        layout = cellpack.Layout()
        # add left button
        if self.info.state == 'downloading':
            left_button = 'pause'
        else:
            left_button = 'resume'
        left_button_rect = layout.add_image(self.button[left_button], 0, 0,
                hotspot=left_button)
        # add right button
        right_x = width - self.button['cancel'].width
        layout.add_image(self.button['cancel'], right_x, 0, hotspot='cancel')
        # pack the progress bar in the center
        progress_left = left_button_rect.width + 2
        progress_right = right_x - 2
        progress_rect = cellpack.LayoutRect(progress_left, 0,
                progress_right-progress_left, height)

        layout.add_rect(progress_rect, ItemProgressBarDrawer(self.info).draw)
        # middle-align everything
        layout.center_y(top=0, bottom=height)
        return layout

    def layout_text(self, layout_manager, width, height):
        """Handle layout when we should display status text"""
        layout = cellpack.Layout()
        text, color = self._calc_status_text()
        if text:
            layout_manager.set_font(self.font_size, bold=True)
            layout_manager.set_text_color(color)
            textbox = layout_manager.textbox(text)
            layout.add_text_line(textbox, 0, 0, width)
            self.add_extra_button(layout, width)
        # middle-align everything
        layout.center_y(top=0, bottom=height)
        return layout

    def _calc_status_text(self):
        """Calculate the text/color for our status line.

        :returns: (text, color) tuple
        """
        if self.info.downloaded:
            if self.info.is_playable:
                if not self.info.video_watched:
                    return (_('Unplayed'), UNPLAYED_COLOR)
                elif self.info.expiration_date:
                    text = displaytext.expiration_date_short(
                            self.info.expiration_date)
                    return (text, EXPIRING_TEXT_COLOR)
        elif (self.info.download_info and
                self.info.download_info.rate == 0):
            if self.info.download_info.state == 'paused':
                return (_('paused'), DOWNLOADING_COLOR)
            elif self.info.download_info.state == 'pending':
                return (_('queued'), DOWNLOADING_COLOR)
            elif self.info.download_info.state == 'failed':
                return (self.info.download_info.short_reason_failed,
                        DOWNLOADING_COLOR)
            else:
                return (self.info.download_info.startup_activity,
                        DOWNLOADING_COLOR)
        elif not self.info.item_viewed:
            return (_('Newly Available'), AVAILABLE_COLOR)
        return ('', self.default_text_color)

    def add_extra_button(self, layout, width):
        """Add a button to the right of the text, if needed"""

        if self.info.expiration_date:
            button_name = 'keep'
        elif (self.info.state == 'downloading' and
              self.info.download_info.state == 'pending'):
            button_name = 'cancel'
        else:
            return
        button = self.button[button_name]
        button_x = width - button.width # right-align
        layout.add_image(button, button_x, 0, hotspot=button_name)

class RatingRenderer(widgetset.InfoListRenderer):
    """Render ratings column

    This cell supports updating based on hover states and rates items based on
    the user clicking in the cell.
    """

    # NOTE: we don't inherit from ListViewRenderer because we handle
    # everything ourselves, without using the Layout class

    ICON_STATES = ('yes', 'no', 'probably', 'unset')
    ICON_HORIZONTAL_SPACING = 2
    ICON_COUNT = 5

    def __init__(self):
        widgetset.InfoListRenderer.__init__(self)
        self.want_hover = True
        self.icon = {}
        # TODO: to support scaling, we need not to check min_height until after
        # the renderer first gets its layout_manager
#        self.icon_height = int(self.height * 9.0 / 14.0)
        self.icon_height = 9
        self.icon_width = self.icon_height
        for state in RatingRenderer.ICON_STATES:
            path = resources.path('images/star-%s.png' % state)
            self.icon[state] = imagepool.get_surface(path,
                               (self.icon_width, self.icon_height))
        self.min_width = self.width = int(self.icon_width * self.ICON_COUNT)
        self.hover = None

    def hotspot_test(self, style, layout_manager, x, y, width, height):
        hotspot_index = self.icon_index_at_x(x)
        if hotspot_index is not None:
            return "rate:%s" % hotspot_index
        else:
            return None

    def icon_index_at_x(self, x):
        """Calculate the index of the icon

        :param x: x-coordinate to use
        :returns: index of the icon at x, or None
        """
        # use icon_width + ICON_HORIZONTAL_SPACING to calculate which star we
        # are over.  Don't worry about the y-coord

        # make each icon's area include the spacing around it
        icon_width_with_pad = self.icon_width + self.ICON_HORIZONTAL_SPACING
        # translate x so that x=0 is to the left of the cell, based on
        # ICON_HORIZONTAL_SPACING.  This effectively centers the spacing on
        # each icon, rather than having the spacing be to the right.
        x += int(self.ICON_HORIZONTAL_SPACING / 2)
        # finally, calculate which icon is hit
        if 0 <= x < icon_width_with_pad * self.ICON_COUNT:
            return int(x // icon_width_with_pad) + 1
        else:
            return None

    def get_size(self, style, layout_manager):
        return self.width, self.icon_height

    def render(self, context, layout_manager, selected, hotspot, hover):
        if hover:
            self.hover = self.icon_index_at_x(hover[0])
        else:
            self.hover = None
        x_pos = 0
        y_pos = int((context.height - self.icon_height) / 2)
        for i in xrange(self.ICON_COUNT):
            icon = self._get_icon(i + 1)
            icon.draw(context, x_pos, y_pos, icon.width, icon.height)
            x_pos += self.icon_width + self.ICON_HORIZONTAL_SPACING

    def _get_icon(self, i):
        """Get the ith rating icon, starting at 1.

        :returns: ImageSurface
        """
        # yes/no for explicit ratings; maybe/no for hover ratings;
        # probably/no for auto ratings; unset when no explicit, auto, or hover rating
        if self.hover is not None:
            if self.hover >= i:
                state = 'yes'
            else:
                state = 'no'
        else:
            if self.info.rating is not None:
                if self.info.rating >= i:
                    state = 'yes'
                else:
                    state = 'no'
            elif self.info.auto_rating is not None:
                if self.info.auto_rating >= i:
                    state = 'probably'
                else:
                    state = 'unset'
            else:
                state = 'unset'
        return self.icon[state]

class StateCircleRenderer(widgetset.InfoListRenderer):
    """Renderer for the state circle column."""

    # NOTE: we don't inherit from ListViewRenderer because we handle
    # everything ourselves, without using the Layout class

    ICON_STATES = ('unplayed', 'new', 'playing', 'downloading')
    ICON_PROPORTIONS = 7.0 / 9.0 # width / height
    min_width = 7
    min_height = 9

    def __init__(self):
        widgetset.InfoListRenderer.__init__(self)
        self.icon = {}
        self.setup_size = (-1, -1)

    def setup_icons(self, width, height):
        """Create icons that will fill our allocated area correctly. """
        if (width, height) == self.setup_size:
            return

        print "SETUP: ", width, height

        icon_width = int(height / 2.0)
        icon_height = int((icon_width / self.ICON_PROPORTIONS) + 0.5)
        # FIXME: by the time min_width is set below, it doesn't matter --Kaz
        self.width = self.min_width = icon_width
        self.height = icon_height
        icon_dimensions = (icon_width, icon_height)
        for state in StateCircleRenderer.ICON_STATES:
            path = resources.path('images/status-icon-%s.png' % state)
            self.icon[state] = imagepool.get_surface(path, icon_dimensions)
        self.setup_size = (width, height)

    def get_size(self, style, layout_manager):
        return self.min_width, self.min_height

    def hotspot_test(self, style, layout_manager, x, y, width, height):
        return None

    def render(self, context, layout_manager, selected, hotspot, hover):
        self.setup_icons(context.width, context.height)
        icon = self.calc_icon()
        # center icon vertically and horizontally
        x = int((context.width - self.width) / 2)
        y = int((context.height - self.height) / 2)
        if icon:
            icon.draw(context, x, y, icon.width, icon.height)

    def calc_icon(self):
        """Get the icon we should show.

        :returns: ImageSurface to display
        """
        if self.info.state == 'downloading':
            return self.icon['downloading']
        elif self.info.is_playing:
            return self.icon['playing']
        elif self.info.state == 'newly-downloaded':
            return self.icon['unplayed']
        elif self.info.downloaded and self.info.is_playable and not self.info.video_watched:
            return self.icon['new']
        elif (not self.info.item_viewed and not self.info.expiration_date and
                not self.info.is_external and not self.info.downloaded):
            return self.icon['new']
        else:
            return None

class ProgressBarColorSet(object):
    PROGRESS_BASE_TOP = (0.92, 0.53, 0.21)
    PROGRESS_BASE_BOTTOM = (0.90, 0.45, 0.08)
    BASE = (0.76, 0.76, 0.76)

    PROGRESS_BORDER_TOP = (0.80, 0.51, 0.28)
    PROGRESS_BORDER_BOTTOM = (0.76, 0.44, 0.16)
    PROGRESS_BORDER_HIGHLIGHT = (1.0, 0.68, 0.42)

    BORDER_GRADIENT_TOP = (0.58, 0.58, 0.58)
    BORDER_GRADIENT_BOTTOM = (0.68, 0.68, 0.68)

class ProgressBarDrawer(cellpack.Packer):
    """Helper object to draw the progress bar (which is actually quite
    complicated.
    """

    def __init__(self, progress_ratio, color_set):
        self.progress_ratio = progress_ratio
        self.color_set = color_set

    def _layout(self, context, x, y, width, height):
        self.x, self.y, self.width, self.height = x, y, width, height
        context.set_line_width(1)
        self.progress_width = int(width * self.progress_ratio)
        self.half_height = height / 2
        if self.progress_width < self.half_height:
            self.progress_end = 'left'
        elif width - self.progress_width < self.half_height:
            self.progress_end = 'right'
        else:
            self.progress_end = 'middle'
        self._draw_base(context)
        self._draw_border(context)

    def _draw_base(self, context):
        # set the clip region to be the outline of the progress bar.  This way
        # we can just draw rectangles and not have to worry about the circular
        # edges.
        context.save()
        self._outer_border(context)
        context.clip()
        # draw our rectangles
        self._progress_top_rectangle(context)
        context.set_color(self.color_set.PROGRESS_BASE_TOP)
        context.fill()
        self._progress_bottom_rectangle(context)
        context.set_color(self.color_set.PROGRESS_BASE_BOTTOM)
        context.fill()
        self._non_progress_rectangle(context)
        context.set_color(self.color_set.BASE)
        context.fill()
        # restore the old clipping region
        context.restore()

    def _draw_border(self, context):
        # Set the clipping region to be the on the border of the progress bar.
        # This is a little tricky.  We have to make a path around the outside
        # of the border that goes in one direction, then a path that is inset
        # by 1 px going the other direction.  This causes the clip region to
        # be the 1 px area between the 2 paths.
        context.save()
        self._outer_border(context)
        self._inner_border(context)
        context.clip()
        # Render the borders
        self._progress_top_rectangle(context)
        context.set_color(self.color_set.PROGRESS_BORDER_TOP)
        context.fill()
        self._progress_bottom_rectangle(context)
        context.set_color(self.color_set.PROGRESS_BORDER_BOTTOM)
        context.fill()
        self._non_progress_rectangle(context)
        gradient = widgetset.Gradient(self.x + self.progress_width, self.y,
                                      self.x + self.progress_width, self.y + self.height)
        gradient.set_start_color(self.color_set.BORDER_GRADIENT_TOP)
        gradient.set_end_color(self.color_set.BORDER_GRADIENT_BOTTOM)
        context.gradient_fill(gradient)
        # Restore the old clipping region
        context.restore()
        self._draw_progress_highlight(context)
        self._draw_progress_right(context)

    def _draw_progress_right(self, context):
        if self.progress_width == self.width:
            return
        radius = self.half_height
        if self.progress_end == 'left':
            # need to figure out how tall to draw the border.
            # pythagoras to the rescue
            a = radius - self.progress_width
            upper_height = math.floor(math.sqrt(radius**2 - a**2))
        elif self.progress_end == 'right':
            end_circle_start = self.width - radius
            a = self.progress_width - end_circle_start
            upper_height = math.floor(math.sqrt(radius**2 - a**2))
        else:
            upper_height = self.height / 2
        top = self.y + (self.height / 2) - upper_height
        context.rectangle(self.x + self.progress_width-1, top, 1, upper_height)
        context.set_color(self.color_set.PROGRESS_BORDER_TOP)
        context.fill()
        context.rectangle(self.x + self.progress_width-1, top + upper_height,
                1, upper_height)
        context.set_color(self.color_set.PROGRESS_BORDER_BOTTOM)
        context.fill()

    def _draw_progress_highlight(self, context):
        width = self.progress_width - 2 # highlight is 1 px in on both sides
        if width <= 0:
            return
        radius = self.half_height - 2
        left = self.x + 1.5 # start 1 px to the right of self.x
        top = self.y + 1.5
        context.move_to(left, top + radius)
        if self.progress_end == 'left':
            # need to figure out the angle to end on, use some trig
            length = float(radius - width)
            theta = -(PI / 2) - math.asin(length/radius)
            context.arc(left + radius, top + radius, radius, -PI, theta)
        else:
            context.arc(left + radius, top + radius, radius, -PI, -PI/2)
            # draw a line to the right end of the progress bar (but don't go
            # past the circle on the right side)
            x = min(left + width,
                    self.x + self.width - self.half_height - 0.5)
            context.line_to(x, top)
        context.set_color(self.color_set.PROGRESS_BORDER_HIGHLIGHT)
        context.stroke()

    def _outer_border(self, context):
        widgetutil.circular_rect(context, self.x, self.y,
                self.width, self.height)

    def _inner_border(self, context):
        widgetutil.circular_rect_negative(context, self.x + 1, self.y + 1,
                self.width - 2, self.height - 2)

    def _progress_top_rectangle(self, context):
        context.rectangle(self.x, self.y,
                self.progress_width, self.half_height)

    def _progress_bottom_rectangle(self, context):
        context.rectangle(self.x, self.y + self.half_height,
                self.progress_width, self.half_height)

    def _non_progress_rectangle(self, context):
        context.rectangle(self.x + self.progress_width, self.y,
                self.width - self.progress_width, self.height)

class ItemProgressBarDrawer(ProgressBarDrawer):
    def __init__(self, info):
        ProgressBarDrawer.__init__(self, 0, ProgressBarColorSet)
        if info.download_info and info.size > 0.0:
            self.progress_ratio = (float(info.download_info.downloaded_size) /
                    info.size)
        else:
            self.progress_ratio = 0.0
