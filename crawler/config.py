import random

user_agents = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36 115Browser/6.0.3',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; MALC; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; BOIE9;ENUSMSN; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
]


def get_headers():
    """
    :return: a random user agent
    """
    return {
        'User-Agent': random.choice(user_agents),
        'Cookie': "b_ut=5; i-wanna-go-back=-1; buvid3=F7AF42A9-726D-42F7-822A-AF5B06CD3F01167618infoc; b_nut=16322965"
                  "84; fingerprint=bd229a476cee98d9a5b6bdbaf6e154b9; buvid_fp=e9cc9516295e5f45b01714e70529cccf; "
                  "buvid_fp_plain=undefined; CURRENT_BLACKGAP=0; CURRENT_FNVAL=4048; PVID=2; blackside_state=0; "
                  "LIVE_BUVID=AUTO6916378289430118; buvid4=E3D4EF5D-DC34-5068-E6D9-888F5E3B03DB05361-022021913-TTYbA0S"
                  "qlf37OrVgZrfagQ%3D%3D; nostalgia_conf=-1; _uuid=331029A10C-4F510-81E1-D5710-C698BDC6489A75437infoc; "
                  "bp_video_offset_387323308=738683694475116700; CURRENT_QUALITY=120; b_nut=100; is-2022-channel=1; "
                  "rpdid=|(k~mkJu||~)0J'uYY)Y~)R||; SESSDATA=785b81ef%2C1686560377%2C9b4fc%2Ac1; "
                  "bili_jct=dcbdf14edf1364e70442eedb60301881; DedeUserID=387323308; DedeUserID__ckMd5=9be58e3592ca2151;"
                  " sid=7jzetobr; innersign=1; b_lsid=E7493A8E_185102D2830; theme_style=light; bsource=search_baidu"
    }
