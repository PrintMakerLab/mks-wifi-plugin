# Copyright (c) 2022
# MKS Plugin is released under the terms of the AGPLv3 or higher.

# To run unit tests:
# 1. install pytest: https://docs.pytest.org/en/latest/getting-started.html
# 2. copy Uranium (https://github.com/Ultimaker/Uranium/tree/master/UM) to python libs folder (ex.: C:\Program Files\Python310\Lib)
# 3. - run tests from command line: python -m pytest
#    - run tests from Visual Studio Code: https://code.visualstudio.com/docs/python/testing

import utils

def test_generate_new_filename_without_truncation():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abcd.gcode',
        max_filename=30,
        existing_sd_files=[],
        expected_sd_files=[
            'abcd.gcode',
            'abcd1.gcode',
            'abcd2.gcode',
            'abcd3.gcode',
            'abcd4.gcode',
            'abcd5.gcode',
            'abcd6.gcode',
            'abcd7.gcode',
            'abcd8.gcode',
            'abcd9.gcode',
            'abcd10.gcode',
            'abcd11.gcode']
    )

def test_generate_new_filename_with_truncation_after_10_chars():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=10,
        existing_sd_files=[],
        expected_sd_files=[
            'abc.gcode',
            'abc1.gcode',
            'abc2.gcode',
            'abc3.gcode',
            'abc4.gcode',
            'abc5.gcode',
            'abc6.gcode',
            'abc7.gcode',
            'abc8.gcode',
            'abc9.gcode',
            'ab10.gcode',
            'ab11.gcode']
    )

def test_generate_new_filename_with_truncation_after_9_chars():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=9,
        existing_sd_files=[],
        expected_sd_files=[
            'abc.gcode',
            'ab1.gcode',
            'ab2.gcode',
            'ab3.gcode',
            'ab4.gcode',
            'ab5.gcode',
            'ab6.gcode',
            'ab7.gcode',
            'ab8.gcode',
            'ab9.gcode',
            'a10.gcode',
            'a11.gcode']
    )

def test_generate_new_filename_with_truncation_after_8_chars():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=8,
        existing_sd_files=[],
        expected_sd_files=[
            'ab.gcode',
            'a1.gcode',
            'a2.gcode',
            'a3.gcode',
            'a4.gcode',
            'a5.gcode',
            'a6.gcode',
            'a7.gcode',
            'a8.gcode',
            'a9.gcode',
            '10.gcode',
            '11.gcode']
    )

def test_generate_new_filename_with_truncation_after_7_chars():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=7,
        existing_sd_files=[],
        expected_sd_files=[
            'a.gcode',
            '1.gcode',
            '2.gcode',
            '3.gcode',
            '4.gcode',
            '5.gcode',
            '6.gcode',
            '7.gcode',
            '8.gcode',
            '9.gcode',
            '10.gcode',
            '11.gcode']
    )

def test_generate_new_filename_with_truncation_after_6_chars():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=6,
        existing_sd_files=[],
        expected_sd_files=[
            '.gcode',
            '1.gcode',
            '2.gcode',
            '3.gcode',
            '4.gcode',
            '5.gcode',
            '6.gcode',
            '7.gcode',
            '8.gcode',
            '9.gcode',
            '10.gcode',
            '11.gcode']
    )

def test_generate_new_filename_with_truncation_after_5_chars():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=5,
        existing_sd_files=[],
        expected_sd_files=[
            '.gcode',
            '1.gcode',
            '2.gcode',
            '3.gcode',
            '4.gcode',
            '5.gcode',
            '6.gcode',
            '7.gcode',
            '8.gcode',
            '9.gcode',
            '10.gcode',
            '11.gcode']
    )

def test_generate_new_filename_when_max_filename_0():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=0,
        existing_sd_files=[],
        expected_sd_files=[
            '.gcode',
            '1.gcode',
            '2.gcode',
            '3.gcode',
            '4.gcode',
            '5.gcode',
            '6.gcode',
            '7.gcode',
            '8.gcode',
            '9.gcode',
            '10.gcode',
            '11.gcode']
    )

def test_generate_new_filename_for_abc1_when_it_already_exists():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc1.gcode',
        max_filename=30,
        existing_sd_files=['abc1.gcode'],
        expected_sd_files=[
            'abc1.gcode',
            'abc11.gcode',
            'abc12.gcode',
            'abc13.gcode',
            'abc14.gcode',
            'abc15.gcode',
            'abc16.gcode',
            'abc17.gcode',
            'abc18.gcode',
            'abc19.gcode',
            'abc110.gcode',
            'abc111.gcode',
            'abc112.gcode']
    )

def test_generate_new_filename_for_abc_when_abc5_already_exists():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc.gcode',
        max_filename=30,
        existing_sd_files=['abc5.gcode'],
        expected_sd_files=[
            'abc5.gcode',
            'abc.gcode',
            'abc1.gcode',
            'abc2.gcode',
            'abc3.gcode',
            'abc4.gcode',
            'abc6.gcode',
            'abc7.gcode',
            'abc8.gcode',
            'abc9.gcode',
            'abc10.gcode',
            'abc11.gcode',
            'abc12.gcode']
    )

def test_generate_new_filename_for_file_without_extension():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='abc',
        max_filename=30,
        existing_sd_files=[],
        expected_sd_files=[
            'abc',
            'abc1',
            'abc2',
            'abc3',
            'abc4',
            'abc5',
            'abc6',
            'abc7',
            'abc8',
            'abc9',
            'abc10',
            'abc11']
    )

def test_generate_new_filename_for_file_with_only_extension():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='.gcode',
        max_filename=30,
        existing_sd_files=[],
        expected_sd_files=[
            '.gcode',
            '1.gcode',
            '2.gcode',
            '3.gcode',
            '4.gcode',
            '5.gcode',
            '6.gcode',
            '7.gcode',
            '8.gcode',
            '9.gcode',
            '10.gcode',
            '11.gcode']
    )

def test_generate_new_filename_for_file_with_gco_extension():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='.gco',
        max_filename=30,
        existing_sd_files=[],
        expected_sd_files=[
            '.gco',
            '1.gco',
            '2.gco',
            '3.gco',
            '4.gco',
            '5.gco',
            '6.gco',
            '7.gco',
            '8.gco',
            '9.gco',
            '10.gco',
            '11.gco']
    )

def test_generate_new_filename_hardname():
    simulate_printing_and_validate_result(
        repeat_count=12,
        filename='aBc$.de..ext',
        max_filename=30,
        existing_sd_files=[],
        expected_sd_files=[
            'aBc$.de..ext',
            'aBc$.de.1.ext',
            'aBc$.de.2.ext',
            'aBc$.de.3.ext',
            'aBc$.de.4.ext',
            'aBc$.de.5.ext',
            'aBc$.de.6.ext',
            'aBc$.de.7.ext',
            'aBc$.de.8.ext',
            'aBc$.de.9.ext',
            'aBc$.de.10.ext',
            'aBc$.de.11.ext']
    )

def simulate_printing_and_validate_result(repeat_count, filename, max_filename, existing_sd_files, expected_sd_files):
    for _ in range(repeat_count):
        file = utils.generate_new_filename(existing_sd_files, filename, max_filename)
        existing_sd_files.append(file)
    
    assert existing_sd_files == expected_sd_files
