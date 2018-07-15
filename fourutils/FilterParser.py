from typing import Iterator, Tuple, Optional
import re


class FilterParser(object):
    expression = re.compile(r'(?:([\w\d]+):(?:"(.+)"|((?!")\S+)))')

    def match(self, key: str, query_str: str) -> Optional[Tuple[str, str]]:
        for m_key, m_value in self.match_all(query_str):
            if m_key == key:
                return m_value
        return None

    def match_all(self, query_str: str) -> Iterator[Tuple[str, str]]:
        for res in self.expression.finditer(query_str):
            val = res.group(2) or res.group(3)
            yield res.group(1), val

    def clear_filters(self, query_str: str) -> str:
        return self.expression.sub('', query_str).strip()
