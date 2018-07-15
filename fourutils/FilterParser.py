from typing import Iterator, Tuple, Optional
import re


class FilterParser(object):
    def match(self, key: str, query_str: str) -> Optional[Tuple[str, str]]:
        for m_key, m_value in self.match_all(query_str):
            if m_key == key:
                return m_key, m_value
        return None

    def match_all(self, query_str: str) -> Iterator[Tuple[str, str]]:
        expr = re.compile(r'(?:([\w\d]+):(?:"(.+)"|((?!")\S+)))')
        for res in expr.finditer(query_str):
            val = res.group(2) or res.group(3)
            yield res.group(1), val

    def clear_filters(self, query_str: str) -> str:
        return re.sub(r'\w+:(?:"(.+)"|((?!")\S)+)', '', query_str)\
                 .strip()
