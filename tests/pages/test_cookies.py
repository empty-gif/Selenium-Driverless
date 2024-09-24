import pytest
import uuid
import datetime
from urllib import parse
from selenium_driverless.webdriver import Chrome, Target


async def get_del_cookie_test(target: Target, subtests, test_server):
    name = uuid.uuid4().hex
    value = uuid.uuid4().hex
    domain = "localhost"
    expires = datetime.datetime.utcnow() + datetime.timedelta(days=30)

    args = {
        "name": name,
        "value": value,
        "expires": expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "domain": domain

    }
    url = test_server.url + "/cookie_setter?" + parse.urlencode(args)

    cookies = await target.get_cookies()
    with subtests.test():
        assert len(cookies) == 0

    await target.get(url)
    cookies = await target.get_cookies()
    with subtests.test():
        assert len(cookies) == 1
    cookie = cookies[0]

    for key in ["name", "value", "domain", "path"]:
        with subtests.test(key=key):
            assert cookie["name"] == name
    with subtests.test():
        assert abs(expires - datetime.datetime.utcfromtimestamp(cookie["expires"])) < datetime.timedelta(seconds=1)
        # +- one second
    with subtests.test():
        await target.get(url)
        await target.delete_cookie(name, domain="localhost")


async def assert_n_cookies(target1, target2, n1, n2, subtests):
    cookies1 = await target1.get_cookies()
    cookies2 = await target2.get_cookies()
    with subtests.test():
        assert len(cookies1) == n1
    with subtests.test():
        assert len(cookies2) == n2


async def isolation_test(target1, target2, driver: Chrome, test_server, subtests):
    url = test_server.url + "/cookie_setter?name=test&value=test"
    await assert_n_cookies(target1, target2, 0, 0, subtests)
    await target1.get(url)
    await assert_n_cookies(target1, target2, 1, 0, subtests)
    await target1.delete_all_cookies()
    await target2.delete_all_cookies()
    await assert_n_cookies(target1, target2, 0, 0, subtests)


@pytest.mark.asyncio
async def test_get_del_cookie(h_driver, subtests, test_server):
    target = h_driver.current_target
    context = await h_driver.new_context()
    isolated = context.current_target
    with subtests.test():
        await get_del_cookie_test(target, subtests, test_server)
    with subtests.test():
        await get_del_cookie_test(isolated, subtests, test_server)

    await isolation_test(isolated, target, h_driver, test_server, subtests)
    await isolation_test(target, isolated, h_driver, test_server, subtests)
    context2 = await h_driver.new_context()
    await isolation_test(context2.current_target, isolated, h_driver, test_server, subtests)

# todo: test set cookie
