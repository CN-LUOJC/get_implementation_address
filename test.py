import requests
import brotli

url = "https://app.dedaub.com/polygon/address/0x5c8da63546955ae36d2634cdafd0ff85b8d398d1/decompiled"

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "max-age=0",
    "Referer": "https://app.dedaub.com/decompile?network=ethereum",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    # 注意这里的 Cookie 需要完整粘贴
    "Cookie": "_ga=GA1.1.1823056202.1761552736; hubspotutk=e8b50b5b13730b3ce7b0dc544d43faa9; _hjSessionUser_3862678=eyJpZCI6IjRhMTAzY2MyLWNlMDQtNTRlMC05OWQ4LWQwYjYwOTQ1YTNmMCIsImNyZWF0ZWQiOjE3NjE1NTI3NDk0MjQsImV4aXN0aW5nIjp0cnVlfQ==; _gcl_au=1.1.796026026.1761552736.1365142934.1761736227.1761736423; CookieConsent=true; __Host-next-auth.csrf-token=302bc3bdc05591b9ad6d3fa54025c34f96e9d4a0150a179bc757941139fbdcba%7C1515c76fa3f2f16156b6fd150aa2b10876cccb4d4de365f8a4998e73c07edc08; __Secure-next-auth.callback-url=https%3A%2F%2Fapp.dedaub.com; _hjSession_3862678=eyJpZCI6ImM0NzUyMmNkLWQ4MTgtNDVjMC1hYmMzLWZlNjI3ODdjMzdlZSIsImMiOjE3NjcwMDA5NDU1MTIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; __hstc=42676154.e8b50b5b13730b3ce7b0dc544d43faa9.1761552751107.1766980368668.1767000947400.97; __hssrc=1; cf_clearance=1psFQA_HUe00IBP1r8TuoNymWhixrPS_E9YBrvA2.Bc-1767003175-1.2.1.1-xdkx.aLHqUy0COGnhNyIDSwWhaHsUnZhUdsxwc8qhqKkzxk.r3.IYfYi2qEq0e2kUZPjcTsRSSo87EoEkMHlIedf.84lca308Oix7xIpBBH0da7KcxVkVtM7lZ2JrP6ig4ofcZNVylhE5hFD4rTwcOIdGG_HZgOiGSmdHoxwAaPptY_W2Vh4bz.kvVGxu6UpRg5XdtL.cbTp76JG906hO1UVTQ9Afi6uBWtAcZdA0E"
}

response = requests.get(url, headers=headers)

# 输出响应内容
content = brotli.decompress(response.content)
print(content.decode('utf-8'))
