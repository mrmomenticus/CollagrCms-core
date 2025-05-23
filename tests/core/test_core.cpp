#include <catch2/catch_test_macros.hpp>
#include <list>
#include "src/core/core.hpp"

auto imageCreated = ImageCreated();

auto images = std::list<std::string_view>{"tests/core/img/input/1.jpg", "tests/core/img/input/2.jpg",
                                             "tests/core/img/input/3.jpg", "tests/core/img/input/4.jpg",
                                             "tests/core/img/input/5.jpg", "tests/core/img/input/6.jpg",
                                             "tests/core/img/input/7.jpg", "tests/core/img/input/8.jpeg",
                                             "tests/core/img/input/9.jpg"};
TEST_CASE("Test created output image")
{
    const std::string outputPath = "tests/core/img/output/collage.jpg";
    auto test = imageCreated.create(images, outputPath);

    REQUIRE(test.empty() == false);
}