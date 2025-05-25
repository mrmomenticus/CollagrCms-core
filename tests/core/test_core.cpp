#include <catch2/catch_test_macros.hpp>
#include <list>
#include "src/core/core.hpp"
#include "src/core/image.hpp"

auto imageCreated = ImageCreated();


auto images = std::list<Image>{
    Image{"tests/core/img/input/1.jpg", "$10", "Description 1"},
    Image{"tests/core/img/input/2.jpg", "$20", "Description 2"},
    Image{"tests/core/img/input/3.jpg", "$30", "Description 3"},
    Image{"tests/core/img/input/4.jpg", "$40", "Description 4"},
    Image{"tests/core/img/input/5.jpg", "$50", "Description 5"},
    Image{"tests/core/img/input/6.jpg", "$60", "Description 6"},
    Image{"tests/core/img/input/7.jpg", "$70", "Description 7"},
    Image{"tests/core/img/input/8.jpeg", "$80", "Description 8"},
    Image{"tests/core/img/input/9.jpg", "$90", "Description 9"}
};
TEST_CASE("Test created output image")
{
    const std::string outputPath = "tests/core/img/output/collage.jpg";
    auto test = imageCreated.create(images, outputPath);

    REQUIRE(test.empty() == false);
}