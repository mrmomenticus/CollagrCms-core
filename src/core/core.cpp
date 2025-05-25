#include "core.hpp"
#include <list>
#include <opencv4/opencv2/opencv.hpp>
#include <stdexcept>
#include <string>
#include "spdlog/spdlog.h"

// Структура для хранения информации об изображении, цене и описании


const std::string_view ImageCreated::create(std::list<Image> &images,
                                            const std::string    &outputPath)
{
    // Проверка количества изображений
    if (images.size() != 9)
    {
        spdlog::error("Требуется ровно 9 элементов для коллажа 3x3.");
        throw std::runtime_error("Требуется ровно 9 элементов для коллажа 3x3.");
    }

    // Параметры коллажа
    const int cell_img_width  = 800;
    const int cell_img_height = 500; // высота только для изображения
    const int cell_text_height = 150; // высота под текст (цену и описание)
    const int cell_width      = cell_img_width;
    const int cell_height     = cell_img_height + cell_text_height;
    const int cell_margin     = 60; // отступ между ячейками

    const int grid_cols      = 3;
    const int grid_rows      = 3;

    // Итоговые размеры коллажа с учетом отступов
    const int collage_width  = grid_cols * cell_width + (grid_cols + 1) * cell_margin;
    const int collage_height = grid_rows * cell_height + (grid_rows + 1) * cell_margin;

    // Цвет рамки (BGR)
    cv::Scalar border_color(199, 21, 133);
    int border_thickness = 30;

    // Создаём белый холст
    cv::Mat collage(collage_height, collage_width, CV_8UC3, cv::Scalar(255, 255, 255));

    cv::rectangle(collage, cv::Point(0, 0), cv::Point(collage.cols - 1, collage.rows - 1),
                  border_color, border_thickness);

    int idx = 0;
    for (const auto &info : images)
    {
        cv::Mat img = cv::imread(std::string(info.path));
        if (img.empty())
        {
            throw std::runtime_error("Не удалось загрузить изображение: " + std::string(info.path));
        }

        // Масштабирование изображения с сохранением пропорций
        double scale = std::min(
            static_cast<double>(cell_img_width) / img.cols,
            static_cast<double>(cell_img_height) / img.rows
        );
        int new_width  = static_cast<int>(img.cols * scale);
        int new_height = static_cast<int>(img.rows * scale);

        cv::Mat resized_img;
        cv::resize(img, resized_img, cv::Size(new_width, new_height));

        // Создаём ячейку (фон)
        cv::Mat cell(cell_height, cell_width, CV_8UC3, cv::Scalar(255, 255, 255));

        // Центрируем изображение в верхней части ячейки
        int x_offset = (cell_img_width - new_width) / 2;
        int y_offset = (cell_img_height - new_height) / 2;
        resized_img.copyTo(cell(cv::Rect(x_offset, y_offset, new_width, new_height)));

        // Ограничиваем описание 200 символами
        std::string desc = info.description.substr(0, 200);

        // Рисуем цену и описание под изображением
        int base_y = cell_img_height + 30;
        cv::putText(cell, info.price, cv::Point(20, base_y), cv::FONT_HERSHEY_SIMPLEX, 1.0, cv::Scalar(0, 0, 0), 2);

        // Описание может быть длинным, разбиваем на строки по 40 символов
        int desc_y = base_y + 35;
        int max_line_len = 40;
        for (size_t start = 0; start < desc.size(); start += max_line_len) {
            std::string line = desc.substr(start, max_line_len);
            cv::putText(cell, line, cv::Point(20, desc_y), cv::FONT_HERSHEY_SIMPLEX, 0.7, cv::Scalar(80, 80, 80), 1);
            desc_y += 28;
        }

        // Определяем позицию в коллаже с учетом отступов
        int row = idx / grid_cols;
        int col = idx % grid_cols;
        int x   = col * cell_width + (col + 1) * cell_margin;
        int y   = row * cell_height + (row + 1) * cell_margin;

        // Вставляем ячейку в коллаж
        cell.copyTo(collage(cv::Rect(x, y, cell_width, cell_height)));

        ++idx;
    }

    // Сохраняем итоговый коллаж
    std::vector<int> params = {cv::IMWRITE_JPEG_QUALITY, 95};
    cv::imwrite(outputPath, collage, params);
    spdlog::info("Коллаж сохранён в {}", outputPath);
    // Возвращаем путь к коллажу
    return outputPath;
}
