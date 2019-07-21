import qs
import sheets 
def test_find_sleep_times() -> None:
    test_data = sheets.read_log("test-data/sleep_times_log.csv")
    expected = pd.Series(
        pd.to_datetime(["2019-05-11 00:30", "2019-05-11 23:33", "2019-05-13 23:21"]),
        index=pd.to_datetime(["2019-05-10", "2019-05-11", "2019-05-13"]),
    )
    assert (qs.find_sleep_times(test_data) == expected).all()

