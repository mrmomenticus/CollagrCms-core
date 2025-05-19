#include "core.hpp"
#include <opencv2/opencv.hpp>
#include <string>
#include <list>
#include <stdexcept>


const std::string_view ImageCreated::create(std::list<std::string_view> &images){
    // Проверка количества изображений
    if (images.size() != 9) {
        throw std::runtime_error("Требуется ровно 9 изображений для коллажа 3x3.");
    }

    // Размеры коллажа
    const int cell_width = 200;   // ширина одной ячейки
    const int cell_height = 200;  // высота одной ячейки
    const int grid_cols = 3;
    const int grid_rows = 3;
    const int collage_width = cell_width * grid_cols;
    const int collage_height = cell_height * grid_rows;

    // Создаём белый холст
    cv::Mat collage(collage_height, collage_width, CV_8UC3, cv::Scalar(255, 255, 255));

    // Загружаем изображения
    int idx = 0;
    for (const auto& img_path_sv : images) {
        std::string img_path(img_path_sv);
        cv::Mat img = cv::imread(img_path);
        if (img.empty()) {
            throw std::runtime_error("Не удалось загрузить изображение: " + img_path);
        }

        // Масштабируем изображение до размера ячейки
        cv::Mat resized_img;
        cv::resize(img, resized_img, cv::Size(cell_width, cell_height));

        // Определяем позицию в коллаже
        int row = idx / grid_cols;
        int col = idx % grid_cols;
        int x = col * cell_width;
        int y = row * cell_height;

        // Вставляем изображение в холст
        resized_img.copyTo(collage(cv::Rect(x, y, cell_width, cell_height)));

        ++idx;
    }

    // Сохраняем итоговый коллаж
    static const std::string output_path = "output/collage_result.jpg";
    cv::imwrite(output_path, collage);

    // Возвращаем путь к коллажу
    return output_path;
}
