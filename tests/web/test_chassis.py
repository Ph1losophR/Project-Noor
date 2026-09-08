"""The chassis: two doors, one header, the mode toggle as a route, and what an address
Noor does not have answers with."""


def test_the_two_doors_name_both_surfaces_and_ask_nobody_who_they_are(client):
    # Arrange / Act
    answer = client.get("/")

    # Assert
    assert answer.status_code == 200
    assert 'href="/visits"' in answer.text
    assert 'href="/supervisor"' in answer.text
    assert "Field Team" in answer.text
    assert "Supervisor" in answer.text
    for word in ("sign in", "Sign in", "log in", "Log in", "password", "Password"):
        assert word not in answer.text


def test_a_first_arrival_is_stamped_system_so_the_operating_system_decides(client):
    # Arrange / Act
    answer = client.get("/")

    # Assert — `system` matches no rule in the stylesheet, which is how the
    # prefers-color-scheme blocks get to win before anybody has pressed anything (§9).
    assert 'data-theme="system"' in answer.text


def test_the_stamp_follows_the_cookie(client):
    # Arrange
    client.cookies.set("theme", "dark")

    # Act
    answer = client.get("/")

    # Assert
    assert 'data-theme="dark"' in answer.text


def test_a_theme_cookie_nobody_set_is_ignored_rather_than_stamped(client):
    # Arrange — a cookie is something a person can type
    client.cookies.set("theme", '"><script>')

    # Act
    answer = client.get("/")

    # Assert
    assert 'data-theme="system"' in answer.text
    assert "<script>" not in answer.text


def test_the_first_press_of_the_toggle_asks_for_dark(client):
    # Arrange / Act
    answer = client.post("/theme", data={"back": "/"}, follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    assert answer.headers["location"] == "/"
    assert answer.cookies["theme"] == "dark"


def test_the_next_press_asks_for_light_again(client):
    # Arrange
    client.cookies.set("theme", "dark")

    # Act
    answer = client.post("/theme", data={"back": "/"}, follow_redirects=False)

    # Assert
    assert answer.cookies["theme"] == "light"


def test_the_toggle_returns_to_the_page_it_was_pressed_on_query_and_all(client):
    # Arrange / Act
    answer = client.post("/theme", data={"back": "/visits?day=2026-08-28"},
                         follow_redirects=False)

    # Assert — flipping the mode on a particular day must not silently drop the day
    assert answer.headers["location"] == "/visits?day=2026-08-28"


def test_the_toggle_cannot_be_made_to_send_anybody_off_this_machine(client):
    # Arrange / Act
    answer = client.post("/theme", data={"back": "https://elsewhere.example/x?y=1"},
                         follow_redirects=False)

    # Assert
    assert answer.headers["location"] == "/x?y=1"


def test_a_toggle_with_nowhere_to_return_to_goes_to_the_doors(client):
    # Arrange / Act
    answer = client.post("/theme", data={"back": ""}, follow_redirects=False)

    # Assert
    assert answer.headers["location"] == "/"


def test_every_page_carries_the_form_that_returns_to_it(client):
    # Arrange / Act
    answer = client.get("/")

    # Assert
    assert '<input type="hidden" name="back" value="/">' in answer.text


def test_an_address_noor_does_not_have_is_answered_in_words_with_a_way_back(client):
    # Arrange / Act
    answer = client.get("/no-such-place")

    # Assert — a dead end a person cannot leave is worse than the dead end
    assert answer.status_code == 404
    assert "No such page" in answer.text
    assert 'class="wordmark" href="/"' in answer.text


def test_the_stylesheet_is_linked_before_the_print_override(client):
    # Arrange / Act
    answer = client.get("/")

    # Assert — §10's forced light wins in print by source order at equal specificity
    assert answer.text.index("/static/noor.css") < answer.text.index("/static/print.css")


def test_the_stylesheet_and_a_face_are_served_off_disk(client):
    # Arrange / Act
    css = client.get("/static/noor.css")
    face = client.get("/static/fonts/DMSans-Regular.woff2")

    # Assert — self-hosted, so the demo works with the network unplugged (§12)
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert face.status_code == 200
    assert face.content[:4] == b"wOF2"
