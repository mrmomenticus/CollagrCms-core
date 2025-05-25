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
    const int cellImgWidth  = 800;
    const int cellImgHeight = 500; // высота только для изображения
    const int cellTextHeight = 220; // увеличенная высота под текст (цену и описание)
    const int cellWidth      = cellImgWidth;
    const int cellHeight     = cellImgHeight + cellTextHeight;
    const int cellMargin     = 60; // отступ между ячейками

    const int gridCols      = 3;
    const int gridRows      = 3;

    // Итоговые размеры коллажа с учетом отступов
    const int collageWidth  = gridCols * cellWidth + (gridCols + 1) * cellMargin;
    const int collageHeight = gridRows * cellHeight + (gridRows + 1) * cellMargin;

    // Цвет рамки (BGR)
    cv::Scalar borderColor(126, 100, 126);
    int borderThickness = 30;

    // Создаём белый холст
    cv::Mat collage(collageHeight, collageWidth, CV_8UC3, cv::Scalar(61, 3, 53));

    cv::rectangle(collage, cv::Point(0, 0), cv::Point(collage.cols - 1, collage.rows - 1),
                  borderColor, borderThickness);

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
            static_cast<double>(cellImgWidth) / img.cols,
            static_cast<double>(cellImgHeight) / img.rows
        );
        int newWidth  = static_cast<int>(img.cols * scale);
        int newHeight = static_cast<int>(img.rows * scale);

        cv::Mat resizedImg;
        cv::resize(img, resizedImg, cv::Size(newWidth, newHeight));

        // Создаём ячейку (фон)
        cv::Mat cell(cellHeight, cellWidth, CV_8UC3, cv::Scalar(230, 230, 250));

        // Центрируем изображение по горизонтали и вертикали в области изображения
        int xOffset = (cellImgWidth - newWidth) / 2;
        int yOffset = (cellImgHeight - newHeight) / 2; // теперь по центру по вертикали
        resizedImg.copyTo(cell(cv::Rect(xOffset, yOffset, newWidth, newHeight)));

        // Нарисовать горизонтальную линию-разделитель между изображением и текстом
        int lineY = cellImgHeight + 10; // чуть ниже изображения
        cv::line(cell, cv::Point(0, lineY), cv::Point(cellWidth, lineY), cv::Scalar(180, 180, 180), 10);

        // Ограничиваем описание 300 символами (можно больше, т.к. область увеличена)
        std::string desc;
        if (info.description.length() > 120)
        {
            spdlog::warn("Описание слишком длинное, обрезано.");
            desc = info.description.substr(0, 120);
            desc += "...";
        }
        else {
            desc = info.description;
        }


        // --- Сначала цена (крупно и жирно), потом описание (мелко) ---
        int textMargin = 30;
        int priceFontSize = 2;
        int priceThickness = 2;
        int descFontSize = 1;
        int descThickness = 2;

        // Цена — крупно и жирно, первой строкой
        int priceY = cellImgHeight + textMargin + 50; // чуть ниже линии
        cv::putText(cell, info.price, cv::Point(20, priceY), cv::FONT_HERSHEY_SIMPLEX, priceFontSize, cv::Scalar(20, 20, 20), priceThickness);

        // Описание — под ценой, меньшим шрифтом, перенос по строкам
        int descY = priceY + 60; // отступ после цены
        int maxLineLen = 40; // можно больше, т.к. область шире
        for (size_t start = 0; start < desc.size(); start += maxLineLen) {
            std::string line = desc.substr(start, maxLineLen);
            cv::putText(cell, line, cv::Point(20, descY), cv::FONT_HERSHEY_SIMPLEX, descFontSize, cv::Scalar(5, 5, 5), descThickness);
            descY += 28;
        }

        // Определяем позицию в коллаже с учетом отступов
        int row = idx / gridCols;
        int col = idx % gridCols;
        int x   = col * cellWidth + (col + 1) * cellMargin;
        int y   = row * cellHeight + (row + 1) * cellMargin;

        // Вставляем ячейку в коллаж
        cell.copyTo(collage(cv::Rect(x, y, cellWidth, cellHeight)));

        ++idx;
    }

    // Сохраняем итоговый коллаж
    std::vector<int> params = {cv::IMWRITE_JPEG_QUALITY, 95};
    cv::imwrite(outputPath, collage, params);
    spdlog::info("Коллаж сохранён в {}", outputPath);
    // Возвращаем путь к коллажу
    return outputPath;
}
