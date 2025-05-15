

# **FastAPI**

**版本**: `0.1.0`
**文档格式**: OpenAPI 3.1
**OpenAPI 文件**: [/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## **Endpoints**

### **Projects 模块**
#### **POST /file_parse**
> **描述**: 解析文件（支持本地文件和 S3）

##### **功能说明**
执行将 PDF 转换为 JSON 和 MD 的过程，将生成的 `.json` 和 `.md` 文件输出到指定目录。

##### **参数**
| 参数名              | 类型     | 描述                                                                 |
|---------------------|----------|----------------------------------------------------------------------|
| file_path           | string   | 要解析的 PDF 文件路径。不能与 `file` 同时使用                       |
| parse_method        | string   | 解析方法，可选值：auto、ocr、txt，默认值：auto                     |
| is_json_md_dump     | boolean  | 是否将解析结果写入 .json 和 .md 文件，默认值：false                |
| output_dir          | string   | 输出目录，默认值："output"                                         |
| return_layout       | boolean  | 是否返回解析后的 PDF 布局，默认值：false                           |
| return_info         | boolean  | 是否返回解析后的 PDF 信息，默认值：false                           |
| return_content_list | boolean  | 是否返回解析后的 PDF 内容列表，默认值：false                       |

##### **请求体 (Request Body)**
- **类型**: `multipart/form-data`
- **字段**:
  - `file`: 需要解析的 PDF 文件（二进制数据）

##### **响应**
| 状态码 | 描述               | 返回内容示例                             |
|--------|--------------------|-------------------------------------------|
| 200    | 成功响应            | `"string"`                                |
| 422    | 请求参数验证失败    | `{ "detail": [{ "loc": ["string", 0], "msg": "string", "type": "string" }] }` |
*   **`200 OK`**: 成功响应
    *   内容类型: `application/json`
    *   示例:
        ```json
        "string"
        ```
    *   模式: `字符串`

*   **`422 Unprocessable Entity`**: 验证错误
    *   内容类型: `application/json`
    *   示例:
        ```json
        {
          "detail": [
            {
              "loc": ["string", 0],
              "msg": "string",
              "type": "string"
            }
          ]
        }
        ```
    *   模式: `HTTPValidationError` (参见 模式 部分)

---

## **Schemas**

### **Body_file_parse_file_parse_post**
*   类型: `对象 (object)`
*   属性:
    *   `file` (字符串, 格式: 二进制) - **必需**
```json
{
  "file": "string",
  "file_path": "string",
  "parse_method": "auto",
  "is_json_md_dump": false,
  "output_dir": "output",
  "return_layout": false,
  "return_info": false,
  "return_content_list": false
}
```

### **HTTPValidationError**
*   类型: `对象 (object)`
*   属性:
    *   `detail` (`ValidationError` 数组, 可选)
```json
{
  "detail": [
    {
      "loc": ["string", 0],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

### **ValidationError**
*   类型: `对象 (object)`
*   属性:
    *   `loc` ((字符串 或 整数) 数组) - **必需**
    *   `msg` (字符串) - **必需**
    *   `type` (字符串) - **必需**
```json
{
  "loc": ["string", 0],
  "msg": "string",
  "type": "string"
}
```

