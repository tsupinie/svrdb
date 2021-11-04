

from datetime import datetime, timedelta
import copy
import warnings

try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    import cartopy

    import numpy as np
except ImportError:
    _can_plot = False
else:
    _can_plot = True


_label_conv = {
    'datetime': lambda s: s['datetime'].strftime("%H%M UTC %d %b %Y"),
    'date': lambda s: s['datetime'].strftime("%d %b %Y"),
    'cdate': lambda s: (s['datetime'] - timedelta(hours=12)).strftime("%d %b %Y"),
    'time': lambda s: s['datetime'].strftime("%H%M UTC"),
}


def _get_mpl_transform(crs, ax):
    return cartopy.mpl.geoaxes.InterProjectionTransform(crs, ax.projection) + ax.transData


def _place_label(ax, lab_lon, lab_lat, label_str, align, color):
    ud = align[0]
    lr = align[1]

    ha = {'l':'right', 'c':'center', 'r':'left'}[lr]
    va = {'u':'bottom', 'c':'center', 'l':'top'}[ud]
    off_x = {'l': -1, 'c': 0, 'r':1}[lr]
    off_y = {'u': 1, 'c':0, 'l':-1}[ud]

    map_trans = _get_mpl_transform(cartopy.crs.Geodetic(), ax)

    offset = 3 / 72
    offset_trans = mpl.transforms.ScaledTranslation(off_x * offset, off_y * offset, plt.gcf().dpi_scale_trans)
    text_trans = map_trans + offset_trans

    ax.text(lab_lon, lab_lat, label_str,
            transform=text_trans, ha=ha, va=va, color=color, fontweight='bold', fontsize='small',
            bbox={'boxstyle':'round', 'color':'none', 'ec':color, 'pad':0.1})


def _set_extent(ax, lons, lats):
    lb_lat = min(lats)
    ub_lat = max(lats)
    lb_lon = min(lons)
    ub_lon = max(lons)

    plot_lb_lat = (ub_lat + lb_lat) / 2 - 1.1 * (ub_lat - lb_lat) / 2
    plot_ub_lat = (ub_lat + lb_lat) / 2 + 1.1 * (ub_lat - lb_lat) / 2
    plot_lb_lon = (ub_lon + lb_lon) / 2 - 1.1 * (ub_lon - lb_lon) / 2
    plot_ub_lon = (ub_lon + lb_lon) / 2 + 1.1 * (ub_lon - lb_lon) / 2

    ax.set_extent((plot_lb_lon, plot_ub_lon, plot_lb_lat, plot_ub_lat))


def map_background(plotter):
    def do_plot(svr_list, label=None, filename=None):
        if not _can_plot:
            raise RuntimeError("Must have Matplotlib and Cartopy installed to plot")

        lon_0 = sum(svr_list['slon']) / float(len(svr_list))
        proj = cartopy.crs.LambertConformal(central_longitude=lon_0)

        plt.figure(dpi=150)
        ax = plt.axes(projection=proj)

        plotter(ax, svr_list, label=label)

        states_provinces = cartopy.feature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lakes',
            scale='50m')
        countries = cartopy.feature.NaturalEarthFeature(
            category='cultural',
            name='admin_0_countries_lakes',
            scale='50m')
        ocean = cartopy.feature.NaturalEarthFeature(
            category='physical',
            name='ocean',
            scale='50m')
        urban = cartopy.feature.NaturalEarthFeature(
            category='cultural',
            name='urban_areas',
            scale='50m')
        roads = cartopy.feature.NaturalEarthFeature(
            category='cultural',
            name='roads',
            scale='10m')

        ax.add_feature(urban, edgecolor='none', linewidth=1, facecolor='#dddddd')
        ax.add_feature(roads, edgecolor='#bbbbbb', linewidth=1, facecolor='none')
        ax.add_feature(states_provinces, edgecolor='k', linewidth=1, facecolor='none')
        ax.add_feature(countries, edgecolor='k', linewidth=1, facecolor='none')
        ax.add_feature(ocean, edgecolor='k', linewidth=1, facecolor='#00cccc')

        plt.tight_layout()

        if filename is not None:
            plt.savefig(filename)
        else:
            plt.show()

    return do_plot

@map_background
def plot_tornadoes(ax, tor_list, label=None):
    label_conv = copy.copy(_label_conv)
    label_conv['mag'] = lambda t: "EF%d" % t['mag'] if t['datetime'] >= datetime(2007, 2, 1, 0) else "F%d" % t['mag']

    try:
        label_str = label_conv[label]
    except KeyError:
        label_str = lambda t: str(t[label])

    map_trans = _get_mpl_transform(cartopy.crs.Geodetic(), ax)

    _set_extent(ax, tor_list['start_lon'] + tor_list['end_lon'], tor_list['start_lat'] + tor_list['end_lat'])

    for tor in tor_list:
        is_brief = not (tor['end_lat'] != tor['start_lat'] and tor['end_lon'] != tor['start_lon'])

        if is_brief:
            ax.plot(tor['start_lon'], tor['start_lat'], 'ro', ms=2, mec='none', transform=map_trans)
        else:
            ax.annotate('', xy=(tor['end_lon'], tor['end_lat']), xytext=(tor['start_lon'], tor['start_lat']), 
                xycoords=map_trans,
                arrowprops={'facecolor':'r', 'ec':'none', 'width':2, 'headwidth':2, 'headlength':4},
            )

        if label is not None:
            dlat = tor['end_lat'] - tor['start_lat']
            dlon = tor['end_lon'] - tor['start_lon']
            lab_lat = tor['start_lat'] + dlat / 2
            lab_lon = tor['start_lon'] + dlon / 2

            if is_brief:
                brg_trans = 0
            else:
                u_trans, v_trans = ax.projection.transform_vectors(cartopy.crs.PlateCarree(), np.array([lab_lon]), np.array([lab_lat]), 
                                                               np.array([dlon]), np.array([dlat]))

                brg_trans = np.degrees(np.arctan2(v_trans[0], u_trans[0]))
                if brg_trans > 90:
                    brg_trans -= 180
                if brg_trans < -90:
                    brg_trans += 180

            if -90 <= brg_trans <= -67.5:
                align = 'cl'
            elif -67.5 <= brg_trans <= -22.5:
                align = 'll'
            elif -22.5 <= brg_trans <= 22.5:
                align='lc'
            elif 22.5 <= brg_trans <= 67.5:
                align='lr'
            elif 67.5 <= brg_trans <= 90:
                align='cr'

            _place_label(ax, lab_lon, lab_lat, label_str(tor), align, 'r')

@map_background
def plot_hail(ax, hail_list, label=None):
    label_conv = copy.copy(_label_conv)
    label_conv['mag'] = lambda h: "%.2f" % h['mag']

    try:
        label_str = label_conv[label]
    except KeyError:
        label_str = lambda h: str(h[label])

    map_trans = _get_mpl_transform(cartopy.crs.Geodetic(), ax)

    _set_extent(ax, hail_list['lon'], hail_list['lat'])

    for hail in hail_list:
        ax.plot(hail['lon'], hail['lat'], 'go', ms=2, mec='none', transform=map_trans)

        if label is not None:
            _place_label(ax, hail['lon'], hail['lat'], label_str(hail), 'lc', 'g')


@map_background
def plot_wind(ax, wind_list, label=None):
    label_conv = copy.copy(_label_conv)
    label_conv['mag'] = lambda w: "%s%d" % ((w['mt'][0] if type(w['mt']) != float else ''), w['mag'])

    try:
        label_str = label_conv[label]
    except KeyError:
        label_str = lambda w: str(w[label])

    map_trans = _get_mpl_transform(cartopy.crs.Geodetic(), ax)

    _set_extent(ax, wind_list['lon'], wind_list['lat'])

    for wind in wind_list:
        ax.plot(wind['lon'], wind['lat'], 'bo', ms=2, mec='none', transform=map_trans)

        if label is not None:
            _place_label(ax, wind['lon'], wind['lat'], label_str(wind), 'lc', 'b')

