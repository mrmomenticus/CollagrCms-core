
#include <catch2/catch_test_macros.hpp>
#include <list>
#include "src/core/core.hpp"
#include "src/core/image.hpp"

auto imageCreated = ImageCreated();

auto images = std::list<Image>{
    Image{"tests/core/img/input/1.jpg", "\"Замок\" значок, 25*70мм, с эффектом \"металлик\"", "1000P"},
    Image{"tests/core/img/input/2.jpg", "Description 2", "5000P"},
    Image{"tests/core/img/input/3.jpg",
          "Descriptionwqfqwfqwfqwfqwfqwfqwfffffffffffffffffffffffffffffffffffffffffffqfwqffffffffff"
          "ffffffffwqfqf 3",
          "300P"},
    Image{"tests/core/img/input/4.jpg", "\"Офисные друзья\" стикерпак, А7, сахарная ламинация ", "250P"},
    Image{"tests/core/img/input/5.jpg",
          "Descriffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
          "ffffffffffffffffffffffffffffffffffffffffffffffffffffffption 5",
          "600P"},
    Image{"tests/core/img/input/6.jpg", "Description 6", "780P"},
    Image{"tests/core/img/input/7.jpg", "Description 7", "260P"},
    Image{"tests/core/img/input/8.jpeg", "\"Летний закат\" брелок двусторонний, акрил с блёстками, 6 см", "10000P"},
    Image{"tests/core/img/input/9.jpg", "\"Оскорблинки\" набор значков, 5 шт. 25 мм и 1 шт. 28*85 м", "500000P"}};
TEST_CASE("Test created output image")
{
    const std::string outputPath = "tests/core/img/output/collage.jpg";
    auto              test       = imageCreated.create(images, outputPath);

    REQUIRE(test.empty() == false);
}
