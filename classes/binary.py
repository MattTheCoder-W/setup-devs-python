import unittest

def binary_sum(bin1: str, bin2: str) -> str:
    """
    Sum up two binary values.

    Arguments:
        bin1 (str): First binary string
        bin2 (str): Second binary string

    Returns:
        str: Sum of two given binary values in string format
    """
    goto_len = max([len(bin1), len(bin2)])
    bin1, bin2 = [format(int(bin1), f"#0{goto_len}"),
            format(int(bin2), f"#0{goto_len}")]
    cache = 0
    output = ''
    for i in range(goto_len)[::-1]:
        cur_val = int(bin1[i]) + int(bin2[i]) + cache
        cache = 0
        if cur_val > 1:
            cache = cur_val - 1
            cur_val = cur_val % 2
        output = f"{cur_val}{output}"
    return output

def binary_sub(bin1: str, bin2: str) -> str:
    """
    Substract two binary values.

    Arguments:
        bin1 (str): First binary string
        bin2 (str): Second binary string

    Returns:
        str: Substract value of two given binary values in string format
    """
    goto_len = max([len(bin1), len(bin2)])
    bin1, bin2 = [format(int(bin1), f"#0{goto_len}"),
            format(int(bin2), f"#0{goto_len}")]
    cache = 0
    output = ''
    for i in range(goto_len)[::-1]:
        cur_val = int(bin1[i]) - int(bin2[i]) - cache
        cache = 0
        if cur_val < 0:
            cache = abs(cur_val)
            cur_val = 1
        output = f"{cur_val}{output}"
    output = output[output.find("1"):]
    return output if len(output) > 0 else "0"


class MathTest(unittest.TestCase):
    def test_binary_sum(self):
        self.assertEqual(binary_sum("010", "1"), "011", "Wrong binary sum")
        self.assertEqual(binary_sum("010", "011"), "101", "Wrong binary sum")

    def test_binary_sub(self):
        self.assertEqual(binary_sub("010", "1"), "1", "Wrong binary substraction")
        self.assertEqual(binary_sub("110", "110"), "0", "Wrong binary substraction")
    
    def test_on_numbers(self):
        self.assertEqual(int(binary_sub(str(bin(20))[2:], str(bin(5))[2:]), 2), 15, "Wrong number math!")


if __name__ == "__main__":
    unittest.main()
