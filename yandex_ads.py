import jnius

_Runnable = jnius.autoclass('java.lang.Runnable')
_PythonSDLActivity = jnius.autoclass('org.renpy.android.PythonSDLActivity')

_BannerAdView = jnius.autoclass('com.yandex.mobile.ads.banner.BannerAdView')
_BannerAdSize = jnius.autoclass('com.yandex.mobile.ads.banner.BannerAdSize')
_AdRequestBuilder = jnius.autoclass('com.yandex.mobile.ads.common.AdRequest$Builder')

_FrameLayoutParams = jnius.autoclass('android.widget.FrameLayout$LayoutParams')
_LinearLayoutParams = jnius.autoclass('android.widget.LinearLayout$LayoutParams')
_Gravity = jnius.autoclass('android.view.Gravity')

_String = jnius.autoclass('java.lang.String')

_MobileAds = jnius.autoclass('com.yandex.mobile.ads.common.MobileAds')

_Log = jnius.autoclass('android.util.Log')

_mActivity = _PythonSDLActivity.mActivity

_TAG = 'REN_YANDEX_ADS'

class _RunnableFunction(jnius.PythonJavaClass):
    __javainterfaces__ = ['java/lang/Runnable']

    def __init__(self, func):
        self.func = func

    @jnius.java_method('()V')
    def run(self):
        self.func()

def _wrap_in_runnable(func):
    return _RunnableFunction(func)

def _wrap_in(cls):
    def wrapper(func):
        return cls(func)
    return wrapper

class CallInUi:
    def __init__(self, func, *args, **kwargs):
        self._runnable = _RunnableFunction(self._run)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def _run(self):
        self._func(*self._args, **self._kwargs)

    def __call__(self):
        _mActivity.runOnUiThread(self._runnable)

def __dummy_func():
    pass

_DummyRunnable = _RunnableFunction(__dummy_func)

#_InitializationListener = jnius.autoclass('com.yandex.mobile.ads.common.InitializationListener')

class _InitializationListenerFunction(jnius.PythonJavaClass):
    __javainterfaces__ = ['com/yandex/mobile/ads/common/InitializationListener']
    __javacontext__ = 'app'

    def __init__(self, func):
        self.func = func

    @jnius.java_method('()V')
    def onInitializationCompleted(self):
        self.func()

class _BannerAdEventListenerLog(jnius.PythonJavaClass):
    __javainterfaces__ = ['com/yandex/mobile/ads/banner/BannerAdEventListener']
    __javacontext__ = 'app'

    @jnius.java_method('()V')
    def onAdLoaded(self):
        _Log.i(_TAG, 'Ad loaded')

    @jnius.java_method('(Lcom/yandex/mobile/ads/common/AdRequestError;)V')
    def onAdFailedToLoad(self, error):
        _Log.w(_TAG, 'Ad loading error: %s' % error.getDescription())

    @jnius.java_method('(Lcom/yandex/mobile/ads/common/ImpressionData;)V')
    def onImpression(self, impressionData):
        _Log.i(_TAG, 'Impression')

    @jnius.java_method('()V')
    def onAdClicked(self):
        _Log.i(_TAG, 'Ad clicked')

    @jnius.java_method('()V')
    def onLeftApplication(self):
        _Log.i(_TAG, 'Left from application')

    @jnius.java_method('()V')
    def onReturnedToApplication(self):
        _Log.i(_TAG, 'Returned to application')

_gravity_names = (
    'BOTTOM', 'TOP', 'CENTER', 'LEFT', 'RIGHT',
    'CENTER_HORIZONTAL', 'CENTER_VERTICAL',
    'FILL', 'FILL_HORIZONTAL', 'FILL_VERTICAL',
    'START', 'END'
)
_gravity_dict = {
    name.lower():getattr(_Gravity, name)
    for name in _gravity_names
}
_gravity_dict[None] = _Gravity.NO_GRAVITY

_excepted_pos_values = (None, ) + _gravity_names + ('under_game', 'above_game')

class BannerWrapper:
    def __init__(self, initial_pos='under_game'):
        self._ad_listener = ad_listener = _BannerAdEventListenerLog()

        self._banner = _BannerAdView(_mActivity)
        self._banner.setBannerAdEventListener(ad_listener)

        self._frame_layout_params = _FrameLayoutParams(
            _FrameLayoutParams.WRAP_CONTENT,
            _FrameLayoutParams.WRAP_CONTENT
        )
        self._frame_layout_params.gravity = _Gravity.CENTER
        self._linear_layout_params = _LinearLayoutParams(
            _LinearLayoutParams.WRAP_CONTENT,
            _LinearLayoutParams.WRAP_CONTENT
        )
        self._container = None

        self._ad_unit_id = None
        self._pos = None
        self._size = None

        self._update_position = CallInUi(self._update_position, self)
        self._update_size = CallInUi(self._update_size, self)
        self._update_unit_id = CallInUi(self._update_unit_id, self)
        self._load_ad = CallInUi(self._load_ad, self)

        self.set_position(initial_pos)
        #self.set_sticky_size(-1)

    @staticmethod
    def _update_position(self):
        banner = self._banner
        pos = self._pos
        if pos is not None:
            pos = pos.lower()
        index = None
        frame = False
        if pos == 'under_game':
            index = 'end'
        elif pos == 'above_game':
            index = 'start'
        elif pos in _gravity_dict:
            frame = True
        else:
            raise ValueError('Pos value should be one of %s, but %s given' % (_excepted_pos_values, pos))

        if frame:
            container = _mActivity.mFrameLayout
            self._frame_layout_params.gravity = _gravity_dict[pos]
            banner.setLayoutParams(self._frame_layout_params)
        else:
            container = _mActivity.mVbox
            banner.setLayoutParams(self._linear_layout_params)

        if self._container:
            self._container.removeView(banner)
        self._container = container

        if index == 'start':
            container.addView(banner, 0)
        else:
            container.addView(banner)

    @staticmethod
    def _update_size(self):
        banner = self._banner
        banner.setAdSize(self._size)

    @staticmethod
    def _update_unit_id(self):
        self._banner.setAdUnitId(self._ad_unit_id)

    @staticmethod
    def _load_ad(self):
        self._banner.loadAd(_AdRequestBuilder().build())

    def set_position(self, pos):
        if self._container and pos == self._pos:
            return
        self._pos = pos
        self._update_position()

    def set_sticky_size(self, width=-1):
        self._set_size(_BannerAdSize.stickySize(_mActivity, width))

    def set_flexible_size(self, width, height):
        self._set_size(_BannerAdSize.flexibleSize(width, height))

    def set_size(self, width, height):
        self._set_size(_BannerAdSize(width, height))

    def _set_size(self, size):
        if self._size is None:
            self._size = size
            self._update_size()
        else:
            raise ValueError('Ad size can not be set twice')

    def set_ad_unit_id(self, ad_unit_id):
        self._ad_unit_id = ad_unit_id
        self._update_unit_id()

    def load_ad(self):
        self._load_ad()

@_wrap_in(_InitializationListenerFunction)
def _initialize_ads_callback():
    _Log.i(_TAG, 'Yandex Ads initialized')

@_wrap_in_runnable
def _initialize_ads():
    _MobileAds.initialize(_mActivity, _initialize_ads_callback)

_mActivity.runOnUiThread(_initialize_ads)

create_banner = BannerWrapper
