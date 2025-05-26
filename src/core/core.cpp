#include "core.hpp"
#include <list>
#include <opencv4/opencv2/opencv.hpp>
#include <stdexcept>
#include <string>
#include "spdlog/spdlog.h"

const std::string_view ImageCreated::create(std::list<Image> &images, const std::string &outputPath)
{
    // Проверка количества изображений
    if (images.size() != 9)
    {
        spdlog::error("Требуется ровно 9 элементов для коллажа 3x3.");
        throw std::runtime_error("Требуется ровно 9 элементов для коллажа 3x3.");
    }

    // Параметры коллажа
    const int cellImgWidth  = 1200;
    const int cellImgHeight = 1200;  // высота ячейки
    const int cellWidth     = cellImgWidth;
    const int cellHeight    = cellImgHeight;
    const int cellMargin    = 60;  // отступ между ячейками

    const int gridCols = 3;
    const int gridRows = 3;

    // Итоговые размеры коллажа с учетом отступов
    const int collageWidth  = gridCols * cellWidth + (gridCols + 1) * cellMargin;
    const int collageHeight = gridRows * cellHeight + (gridRows + 1) * cellMargin;

    // Цвет рамки (BGR)
    cv::Scalar borderColor(126, 100, 126);
    int        borderThickness = 30;

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

        // Масштабирование изображения на всю ячейку с сохранением пропорций и заполнением фона
        double scale     = std::max(static_cast<double>(cellImgWidth) / img.cols,
                                    static_cast<double>(cellImgHeight) / img.rows);
        int    newWidth  = static_cast<int>(img.cols * scale);
        int    newHeight = static_cast<int>(img.rows * scale);

        cv::Mat resizedImg;
        cv::resize(img, resizedImg, cv::Size(newWidth, newHeight));

        // Центрируем изображение по горизонтали и вертикали, обрезаем лишнее
        int      xOffset   = std::max(0, (newWidth - cellImgWidth) / 2);
        int      yOffset   = std::max(0, (newHeight - cellImgHeight) / 2);
        int      roiWidth  = std::min(cellImgWidth, resizedImg.cols - xOffset);
        int      roiHeight = std::min(cellImgHeight, resizedImg.rows - yOffset);
        cv::Rect roi(xOffset, yOffset, roiWidth, roiHeight);
        cv::Mat  cell = resizedImg(roi).clone();

        // Если изображение меньше, чем ячейка, то добавляем белый фон
        if (roiWidth < cellImgWidth || roiHeight < cellImgHeight)
        {
            cv::Mat padded(cellImgHeight, cellImgWidth, cell.type(), cv::Scalar(255, 255, 255));
            cell.copyTo(padded(cv::Rect(0, 0, roiWidth, roiHeight)));
            cell = padded;
        }

        // Полупрозрачный белый фон для текста внизу ---
        int    overlayHeight = 120;  // высота под цену и описание
        double alpha         = 0.5;  // прозрачность

        cv::Mat overlay = cell.clone();
        // Нарисовать overlay внизу
        cv::rectangle(overlay, cv::Point(0, cellImgHeight - overlayHeight),
                      cv::Point(cellImgWidth, cellImgHeight), cv::Scalar(255, 255, 255),
                      cv::FILLED);
        cv::addWeighted(overlay, alpha, cell, 1 - alpha, 0, cell);

        // Ограничиваем описание 120 символами
        std::string desc;
        if (info.description.length() > 50)
        {
            spdlog::warn("{}: Описание слишком длинное, обрезано.", info.path);
            desc = info.description.substr(0, 50);
        }
        else
        {
            desc = info.description;
        }

        // Цена (жирно), затем описание (мелко), оба на белом фоне внизу ---
        int textMarginX    = 30;
        int priceFontSize  = 2;
        int priceThickness = 2;
        int descFontSize   = 1;
        int descThickness  = 2;

        // Цена — первой строкой внизу overlay
        int priceY = cellImgHeight - overlayHeight + 65;  // чуть ниже верхнего края overlay
        cv::putText(cell, info.price, cv::Point(textMarginX, priceY), cv::FONT_HERSHEY_DUPLEX,
                    priceFontSize, cv::Scalar(65, 65, 65), priceThickness);

        // Описание — под ценой, меньшим шрифтом, перенос по строкам
        int descY = priceY + 40;  // отступ после цены
        cv::putText(cell, desc, cv::Point(textMarginX, descY), cv::FONT_HERSHEY_DUPLEX ,
                    descFontSize, cv::Scalar(40, 40, 40), descThickness);

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
