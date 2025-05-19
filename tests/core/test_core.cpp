#include <catch2/catch_test_macros.hpp>
#include <list>
#include "src/core/core.hpp"

auto imageCreated = ImageCreated();

auto images = std::list<std::string_view>{"tests/img/input/1.jpg", "tests/img/input/2.jpg",
                                             "tests/img/input/3.jpg", "tests/img/input/4.jpg",
                                             "tests/img/input/5.jpg", "tests/img/input/6.jpg",
                                             "tests/img/input/7.jpg", "tests/img/input/8.jpg",
                                             "tests/img/input/9.jpg", "tests/img/input/10.jpg"};
TEST_CASE("Test created output image")
{
    std::string_view outputPath = imageCreated.create(images);
    REQUIRE(outputPath.empty() == false);
}