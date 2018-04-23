import pytest
import StocksDasboard.StocksDasboard as sdb


def test_init_variables():
    pytest.raises(AttributeError("'%s cannot be None.'" % "width"), sdb(),
                  width=None)
