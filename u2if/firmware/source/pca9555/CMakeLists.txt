add_library(PCA9555 INTERFACE)

target_sources(PCA9555 INTERFACE
  ${CMAKE_CURRENT_LIST_DIR}/pca9555.cpp
)

target_include_directories(PCA9555 INTERFACE ${CMAKE_CURRENT_LIST_DIR}/include)

target_link_libraries(PCA9555 INTERFACE pico_stdlib hardware_i2c)