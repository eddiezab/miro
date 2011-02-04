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

"""``miro.frontends.widgets.widgetstatestore`` - Stores the state of the
Widgets frontend. See WidgetState design doc.
"""

from miro.messages import SaveDisplayState, SaveViewState, DisplayInfo, ViewInfo

class WidgetStateStore(object):
    LIST_VIEW = 1
    STANDARD_VIEW = 0
    DEFAULT_VIEW_TYPE = {
        u'videos': STANDARD_VIEW,
        u'music': LIST_VIEW,
        u'others': LIST_VIEW,
        u'downloading': STANDARD_VIEW,
        u'all-feeds': STANDARD_VIEW,
        u'feed': STANDARD_VIEW,
        u'search': LIST_VIEW,
        u'sharing': LIST_VIEW,
        u'device-video': STANDARD_VIEW,
        u'device-audio': LIST_VIEW,
        u'playlist': LIST_VIEW,
     }
    FILTER_VIEW_ALL = 0
    FILTER_UNWATCHED = 1
    FILTER_NONFEED = 2
    FILTER_DOWNLOADED = 4
    DEFAULT_DISPLAY_FILTERS = FILTER_VIEW_ALL
    DEFAULT_COLUMN_WIDTHS = {
        u'state': 20,
        u'name': 130,
        u'artist': 110,
        u'album': 100,
        u'track': 30,
        u'feed-name': 70,
        u'length': 60,
        u'genre': 65,
        u'year': 40,
        u'rating': 75,
        u'size': 65,
        u'status': 70,
        u'date': 70,
        u'eta': 60,
        u'torrent-details': 160,
        u'rate': 60,
        u'description': 160,
    }
    DEFAULT_SORT_COLUMN = {
        u'videos': u'name',
        u'music': u'artist',
        u'others': u'name',
        u'downloading': u'eta',
        u'all-feeds': u'feed-name',
        u'feed': u'date',
        u'playlist': u'playlist',
        u'search': u'name',
    }
    DEFAULT_SORT_COLUMN[u'sharing'] = DEFAULT_SORT_COLUMN[u'videos']
    DEFAULT_SORT_COLUMN[u'device-video'] = DEFAULT_SORT_COLUMN[u'videos']
    DEFAULT_SORT_COLUMN[u'device-audio'] = DEFAULT_SORT_COLUMN[u'music']
    DEFAULT_COLUMNS = {
        u'videos':
            [u'state', u'name', u'length', u'feed-name', u'size'],
        u'music':
            [u'state', u'name', u'artist', u'album', u'track',
            u'feed-name', u'length', u'genre', u'year', u'rating'],
        u'others':
            [u'name', u'feed-name', u'size'],
        u'downloading':
            [u'name', u'feed-name', u'status', u'eta', u'rate',
            u'torrent-details', u'size'],
        u'all-feeds':
            [u'state', u'name', u'feed-name', u'length',
            u'status', u'size', u'date'],
        u'feed':
            [u'state', u'name', u'length', u'status', u'size', u'date'],
        u'search':
            [u'state', u'name', u'description'],
    }
    DEFAULT_COLUMNS[u'sharing'] = DEFAULT_COLUMNS[u'videos']
    DEFAULT_COLUMNS[u'device-video'] = DEFAULT_COLUMNS[u'videos']
    DEFAULT_COLUMNS[u'device-audio'] = DEFAULT_COLUMNS[u'music']
    DEFAULT_COLUMNS[u'playlist'] = DEFAULT_COLUMNS[u'music']

    AVAILABLE_COLUMNS = {}
    for display_type, columns in DEFAULT_COLUMNS.items():
        AVAILABLE_COLUMNS[display_type] = DEFAULT_COLUMNS[display_type][:]
    # add available but non-default columns here:
    AVAILABLE_COLUMNS['videos'].extend([u'rating'])
    AVAILABLE_COLUMNS['music'].extend([u'size'])
    AVAILABLE_COLUMNS['others'].extend([u'rating'])
    AVAILABLE_COLUMNS['search'].extend([u'rating'])

    def __init__(self):
        self.displays = {}
        self.views = {}

    def setup_displays(self, message):
        for display in message.displays:
            self.displays[display.key] = display

    def setup_views(self, message):
        for view in message.views:
            self.views[view.key] = view

    def _save_display_state(self, display_type, display_id):
        display = self._get_display(display_type, display_id)
        m = SaveDisplayState(display)
        m.send_to_backend()

    def _save_view_state(self, display_type, display_id, view_type):
        view = self._get_view(display_type, display_id, view_type)
        m = SaveViewState(view)
        m.send_to_backend()

    def _get_display(self, display_type, display_id):
        display_id = unicode(display_id)
        key = (display_type, display_id)
        if not key in self.displays:
            new_display = DisplayInfo(key)
            self.displays[key] = new_display
            self._save_display_state(display_type, display_id)
        return self.displays[key]

    def _get_view(self, display_type, display_id, view_type):
        display_id = unicode(display_id)
        key = (display_type, display_id, view_type)
        if not key in self.views:
            new_view = ViewInfo(key)
            self.views[key] = new_view
            self._save_view_state(display_type, display_id, view_type)
        return self.views[key]

# Real DisplayState Properties:

    def get_selected_view(self, display_type, display_id):
        display = self._get_display(display_type, display_id)
        if display.selected_view is not None:
            view = display.selected_view
        else:
            view = WidgetStateStore.DEFAULT_VIEW_TYPE[display_type]
        return view

    def set_selected_view(self, display_type, display_id, selected_view):
        display = self._get_display(display_type, display_id)
        display.selected_view = selected_view
        self._save_display_state(display_type, display_id)

    def get_filters(self, display_type, display_id):
        display = self._get_display(display_type, display_id)
        if display.active_filters is None:
            return WidgetStateStore.DEFAULT_DISPLAY_FILTERS
        return display.active_filters

    def toggle_filters(self, display_type, display_id, filter_):
        filters = self.get_filters(display_type, display_id)
        filters = WidgetStateStore.toggle_filter(filters, filter_)
        display = self._get_display(display_type, display_id)
        display.active_filters = filters
        self._save_display_state(display_type, display_id)

# ViewState properties that are only valid for specific view_types:

    def get_columns_enabled(self, display_type, display_id, view_type):
        if WidgetStateStore.is_list_view(view_type):
            display = self._get_display(display_type, display_id)
            columns_enabled = display.list_view_columns
            if columns_enabled is not None:
                return columns_enabled
            else:
                return WidgetStateStore.DEFAULT_COLUMNS[display_type]
        else:
            raise ValueError()

    def set_columns_enabled(self, display_type, display_id, view_type, enabled):
        if WidgetStateStore.is_list_view(view_type):
            display = self._get_display(display_type, display_id)
            display.list_view_columns = enabled
            self._save_display_state(display_type, display_id)
        else:
            raise ValueError()

    def toggle_column(self, display_type, display_id, view_type, column):
        if WidgetStateStore.is_list_view(view_type):
            display = self._get_display(display_type, display_id)
            columns_enabled = self.get_columns_enabled(
                              display_type, display_id, view_type)
            if column in columns_enabled:
                columns_enabled.remove(column)
            else:
                columns_enabled.append(column)
            self.set_columns_enabled(display_type, display_id, view_type,
                                    columns_enabled)
        else:
            raise ValueError()

    def get_column_widths(self, display_type, display_id, view_type):
        if WidgetStateStore.is_list_view(view_type):
            display = self._get_display(display_type, display_id)
            column_widths = display.list_view_widths
            if column_widths is not None:
                return column_widths
            else:
                defaults = {}
                for name in self.get_columns_enabled(
                        display_type, display_id, view_type):
                    defaults[name] = WidgetStateStore.DEFAULT_COLUMN_WIDTHS[name]
                return defaults
        else:
            raise ValueError()

    def update_column_widths(self, display_type, display_id, view_type, widths):
        if WidgetStateStore.is_list_view(view_type):
            display = self._get_display(display_type, display_id)
            if display.list_view_widths is None:
                display.list_view_widths = self.get_column_widths(
                                        display_type, display_id, view_type)
            display.list_view_widths.update(widths)
            self._save_display_state(display_type, display_id)
        else:
            raise ValueError()

# Real ViewState properties:

    def get_sort_state(self, display_type, display_id, view_type):
        view = self._get_view(display_type, display_id, view_type)
        sort_state = view.sort_state
        if sort_state is None:
            sort_state = WidgetStateStore.DEFAULT_SORT_COLUMN[display_type]
        if WidgetStateStore.is_standard_view(view_type):
            return sort_state
        else:
            enabled = self.get_columns_enabled(display_type, display_id, view_type)
            column = sort_state.lstrip('-')
            if column not in enabled:
                sort_state = WidgetStateStore.DEFAULT_SORT_COLUMN[display_type]
            return sort_state

    def set_sort_state(self, display_type, display_id, view_type, sort_key):
        view = self._get_view(display_type, display_id, view_type)
        view.sort_state = sort_key
        self._save_view_state(display_type, display_id, view_type)

    def get_scroll_position(self, display_type, display_id, view_type):
        view = self._get_view(display_type, display_id, view_type)
        if view.scroll_position is not None:
            scroll_position = view.scroll_position
        else:
            scroll_position = (0, 0)
        return scroll_position

    def set_scroll_position(self, display_type, display_id, view_type,
            scroll_position):
        view = self._get_view(display_type, display_id, view_type)
        view.scroll_position = scroll_position
        self._save_view_state(display_type, display_id, view_type)

# static properties of a display_type:

    @staticmethod
    def get_columns_available(display_type):
        return WidgetStateStore.AVAILABLE_COLUMNS[display_type]

# static properties of a view_type:

    @staticmethod
    def is_list_view(view_type):
        return view_type == WidgetStateStore.LIST_VIEW

    @staticmethod
    def is_standard_view(view_type):
        return view_type == WidgetStateStore.STANDARD_VIEW

# manipulate a filter set:

    @staticmethod
    def toggle_filter(filters, filter_):
        if filter_ == WidgetStateStore.FILTER_VIEW_ALL:
            return filter_
        else:
            return filters ^ filter_

# static properties of a filter combination:

    @staticmethod
    def is_view_all_filter(filters):
        return filters == WidgetStateStore.FILTER_VIEW_ALL

    @staticmethod
    def has_unwatched_filter(filters):
        return bool(filters & WidgetStateStore.FILTER_UNWATCHED)

    @staticmethod
    def has_non_feed_filter(filters):
        return bool(filters & WidgetStateStore.FILTER_NONFEED)

    @staticmethod
    def has_downloaded_filter(filters):
        return bool(filters & WidgetStateStore.FILTER_DOWNLOADED)

# static properties:

    # displays:

    @staticmethod
    def get_display_types():
        return WidgetStateStore.AVAILABLE_COLUMNS.keys()

    # views:

    @staticmethod
    def get_list_view_type():
        return WidgetStateStore.LIST_VIEW

    @staticmethod
    def get_standard_view_type():
        return WidgetStateStore.STANDARD_VIEW

    # filters:

    @staticmethod
    def get_view_all_filter():
        return WidgetStateStore.FILTER_VIEW_ALL

    @staticmethod
    def get_unwatched_filter():
        return WidgetStateStore.FILTER_UNWATCHED

    @staticmethod
    def get_non_feed_filter():
        return WidgetStateStore.FILTER_NONFEED

    @staticmethod
    def get_downloaded_filter():
        return WidgetStateStore.FILTER_DOWNLOADED