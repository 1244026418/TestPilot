from app.services.ai_case_generator import generate_cases


def test_generate_login_cases():
    cases = generate_cases(
        requirement="用户登录接口，需要校验账号密码和异常参数",
        method="POST",
        url="http://127.0.0.1:8000/demo-target/login",
        body={"username": "demo", "password": "123456"},
        expected_status=200,
    )

    titles = [case["title"] for case in cases]
    assert "正常流程：参数合法时接口返回成功" in titles
    assert any(case["expected_status"] == 401 for case in cases)
    assert any(case["category"] == "boundary" for case in cases)

