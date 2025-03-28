@echo off
chcp 65001
color a
cd VE
:MENU
cls
echo Полный путь: C:\Users\user\AppData\Roaming\com.flauncher.app\FLauncher\VE\build
echo ==========================
echo =Batch File By Zemonkamin=
echo =------------------------=
echo =  Сборка VE на Windows  =
echo ==========================
echo Выберите опцию:
echo Установка зависимостей:
echo 1. Установить Git
echo 2. Установить vcpkg
echo 3. Установить CMake (откроет браузер на странице загрузки)
echo 4. Установить vcpkg libs
echo --------------------------------------
echo Операции с кодом движка:
echo 5. Собрать с Visual Studio 17 2022
echo 6. Собрать с Visual Studio 16 2019
echo 7. Собрать с Visual Studio 15 2017
echo 8. Собрать с Visual Studio 14 2015
echo 9. Удалить папку сборки
echo 10. Открыть папку сборки
echo 11. Запустить движок
echo --------------------------------------
echo 12. Выход
set /p choice=Введите номер опции (1-12): 

if %choice%==1 (
    echo Установка Git...
    powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit', '-Command', 'winget install --id Git.Git -e --source winget'"
    pause
    goto MENU
) else if %choice%==2 (
    echo Установка vcpkg...
    powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit', '-Command', 'cd C:\; if (Test-Path vcpkg) { Remove-Item vcpkg -Recurse -Force }; git clone https://github.com/microsoft/vcpkg.git; cd vcpkg; .\\bootstrap-vcpkg.bat; [Environment]::SetEnvironmentVariable(\"VCPKG_ROOT\", \"C:\\vcpkg\", \"Machine\"); $path = [Environment]::GetEnvironmentVariable(\"Path\", \"Machine\"); [Environment]::SetEnvironmentVariable(\"Path\", \"$path;C:\\vcpkg\", \"Machine\")'"
    echo Vcpkg installed. Please restart this script to apply environment variables.
    pause
    goto MENU
) else if %choice%==3 (
    echo Открытие CMake страницы загрузки...
    start https://cmake.org/download/
    goto MENU
) else if %choice%==4 (
    vcpkg install
    pause
    goto MENU
) else if %choice%==5 (
    if exist build (
        echo Удаление папки сборки...
        rmdir /s /q build
    )
    cmake --preset=default-vs-msvc-windows
    cd build
    cmake --build . --config Release
    cd ..
    pause
    goto MENU
) else if %choice%==6 (
    if exist build (
        echo Удаление папки сборки...
        rmdir /s /q build
    )
    cmake --preset=default-vs-msvc-windows -G "Visual Studio 16 2019"
    cd build
    cmake --build . --config Release
    cd ..
    pause
    goto MENU
) else if %choice%==7 (
    if exist build (
        echo Удаление папки сборки...
        rmdir /s /q build
    )
    cmake --preset=default-vs-msvc-windows -G "Visual Studio 15 2017"
    cd build
    cmake --build . --config Release
    cd ..
    pause
    goto MENU
) else if %choice%==8 (
    if exist build (
        echo Удаление папки сборки...
        rmdir /s /q build
    )
    cmake --preset=default-vs-msvc-windows -G "Visual Studio 14 2015"
    cd build
    cmake --build . --config Release
    cd ..
    pause
    goto MENU
) else if %choice%==9 (
    if exist build (
        echo Удаление папки сборки...
        rmdir /s /q build
        echo Build folder deleted.
    ) else (
        echo Папки сборки не существует.
    )
    pause
    goto MENU
) else if %choice%==10 (
    if exist build\Release (
        echo Открытие папки сборки в Explorer...
        start "" "build\Release"
    ) else (
        echo Папки сборки не существует.
    )
    pause
    goto MENU
) else if %choice%==11 (
    echo Запуск VoxelEngine...
    cd build\Release
    VoxelEngine.exe
    pause
    goto MENU
) else if %choice%==12 (
    color 7
    exit
) else (
    echo Неправильный выбор, попробуйте еще раз.
    pause
    goto MENU
)
