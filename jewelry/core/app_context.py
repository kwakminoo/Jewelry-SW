class AppContext:
    """앱 전역에서 공유되는 상태/서비스 접근점.

    지금은 UI만 구현하는 단계라 비어 있고, storage/devices 서비스가
    생기면 이 클래스를 통해 각 화면에 주입한다.
    """

    def __init__(self) -> None:
        pass
