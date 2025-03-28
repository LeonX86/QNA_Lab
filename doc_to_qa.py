import os
import json
import argparse
import requests
from typing import List, Dict, Any, Optional, Tuple
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理类，负责读取和处理文档内容"""

    def __init__(self, supported_extensions: List[str]):
        """
        初始化文档处理器

        Args:
            supported_extensions: 支持的文件扩展名列表
        """
        self.supported_extensions = supported_extensions

    def read_document(self, file_path: str) -> str:
        """
        读取文档内容

        Args:
            file_path: 文档文件路径

        Returns:
            文档内容字符串

        Raises:
            ValueError: 如果文件格式不支持或文件不存在
        """
        if not os.path.exists(file_path):
            raise ValueError(f"文件不存在: {file_path}")

        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.supported_extensions:
            raise ValueError(f"不支持的文件格式: {ext}. 支持的格式: {', '.join(self.supported_extensions)}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"读取文件时出错: {str(e)}")
            raise

    def split_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        将文档内容分割成小块

        Args:
            content: 文档内容
            chunk_size: 每个块的最大字符数
            overlap: 相邻块之间的重叠字符数

        Returns:
            文档内容块列表
        """
        if not content:
            return []

        chunks = []
        start = 0

        while start < len(content):
            end = min(start + chunk_size, len(content))

            # 如果不是最后一块，尝试在句子或段落边界处分割
            if end < len(content):
                # 尝试在段落边界分割
                paragraph_end = content.rfind('\n\n', start, end)
                if paragraph_end > start + chunk_size // 2:
                    end = paragraph_end + 2
                else:
                    # 尝试在句子边界分割
                    sentence_end = max(
                        content.rfind('. ', start, end),
                        content.rfind('? ', start, end),
                        content.rfind('! ', start, end),
                        content.rfind('\n', start, end)
                    )
                    if sentence_end > start + chunk_size // 2:
                        end = sentence_end + 2

            chunks.append(content[start:end])
            start = end - overlap if end < len(content) else end

        return chunks


class QAGenerator:
    """问答对生成器，使用本地大模型生成问答对"""

    def __init__(self, api_url: str, model: str):
        """
        初始化问答生成器

        Args:
            api_url: API地址
            model: 模型名称
        """
        self.api_url = api_url
        self.model = model

    def generate_qa_pairs(self, document_chunk: str, prompt_template: str) -> List[Dict[str, str]]:
        """
        根据文档块生成问答对

        Args:
            document_chunk: 文档内容块
            prompt_template: 提示模板

        Returns:
            问答对列表
        """
        prompt = prompt_template.format(document=document_chunk)

        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model, "prompt": prompt, "stream": False}
            )

            if response.status_code != 200:
                logger.error(f"API请求失败: {response.status_code}, {response.text}")
                return []

            data = response.json()
            if 'response' not in data:
                logger.error(f"API响应格式错误: {data}")
                return []

            qa_text = data['response']
            return self._parse_qa_response(qa_text)

        except Exception as e:
            logger.error(f"生成问答对时出错: {str(e)}")
            return []

    def _parse_qa_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        解析模型返回的问答文本

        Args:
            response_text: 模型返回的文本

        Returns:
            解析后的问答对列表
        """
        qa_pairs = []

        # 尝试解析不同格式的问答对
        try:
            # 首先尝试直接解析JSON格式
            if response_text.strip().startswith('[') and response_text.strip().endswith(']'):
                try:
                    parsed_data = json.loads(response_text)
                    if isinstance(parsed_data, list):
                        for item in parsed_data:
                            if isinstance(item, dict) and 'question' in item and 'answer' in item:
                                qa_pairs.append({
                                    "prompt": item['question'],
                                    "response": item['answer']
                                })
                        if qa_pairs:
                            return qa_pairs
                except:
                    pass

            # 尝试解析问题和答案格式
            lines = response_text.split('\n')
            i = 0
            while i < len(lines):
                if i + 1 < len(lines):
                    # 查找问题行（通常以Q:、问题:、Question: 等开头）
                    q_line = lines[i].strip()
                    if q_line.startswith(('Q:', '问题:', 'Question:', '问：')) or \
                       (q_line.startswith(('1.', '2.', '3.')) and '?' in q_line):

                        # 提取问题内容
                        question = q_line
                        for prefix in ['Q:', '问题:', 'Question:', '问：']:
                            if question.startswith(prefix):
                                question = question[len(prefix):].strip()
                                break

                        # 如果是数字编号开头，提取问题部分
                        if question[0].isdigit() and question[1:].startswith('. '):
                            question = question[question.find(' ')+1:].strip()

                        # 查找答案行
                        answer_lines = []
                        j = i + 1
                        while j < len(lines) and not (lines[j].strip().startswith(('Q:', '问题:', 'Question:', '问：')) or
                                                     (lines[j].strip().startswith(('1.', '2.', '3.')) and '?' in lines[j].strip())):
                            if lines[j].strip().startswith(('A:', '答案:', 'Answer:', '答：')):
                                answer_line = lines[j].strip()
                                for prefix in ['A:', '答案:', 'Answer:', '答：']:
                                    if answer_line.startswith(prefix):
                                        answer_line = answer_line[len(prefix):].strip()
                                        break
                                answer_lines.append(answer_line)
                            else:
                                answer_lines.append(lines[j].strip())
                            j += 1

                        answer = ' '.join(answer_lines).strip()
                        if question and answer:
                            qa_pairs.append({
                                "prompt": question,
                                "response": answer
                            })

                        i = j - 1  # 更新索引到当前答案的末尾
                i += 1
        except Exception as e:
            logger.error(f"解析问答对时出错: {str(e)}")

        return qa_pairs


class JsonlWriter:
    """JSONL文件写入器"""

    def write_jsonl(self, qa_pairs: List[Dict[str, str]], output_file: str) -> None:
        """
        将问答对写入JSONL文件

        Args:
            qa_pairs: 问答对列表
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for qa_pair in qa_pairs:
                    f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
            logger.info(f"成功写入 {len(qa_pairs)} 个问答对到 {output_file}")
        except Exception as e:
            logger.error(f"写入JSONL文件时出错: {str(e)}")
            raise


class DocumentToQA:
    """文档转问答对主类"""

    def __init__(self,
                 api_url: str,
                 model: str,
                 supported_extensions: List[str],
                 prompt_template: str,
                 output_dir: str):
        """
        初始化文档转问答对处理器

        Args:
            api_url: API地址
            model: 模型名称
            supported_extensions: 支持的文件扩展名列表
            prompt_template: 提示模板
            output_dir: 输出目录
        """
        self.document_processor = DocumentProcessor(supported_extensions)
        self.qa_generator = QAGenerator(api_url, model)
        self.jsonl_writer = JsonlWriter()
        self.prompt_template = prompt_template
        self.output_dir = output_dir

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    def process_document(self, file_path: str, chunk_size: int = 1000, overlap: int = 200) -> str:
        """
        处理文档并生成问答对

        Args:
            file_path: 文档文件路径
            chunk_size: 文档分块大小
            overlap: 分块重叠大小

        Returns:
            输出文件路径
        """
        # 读取文档
        logger.info(f"正在读取文档: {file_path}")
        content = self.document_processor.read_document(file_path)

        # 分割文档
        logger.info(f"正在分割文档，块大小: {chunk_size}，重叠大小: {overlap}")
        chunks = self.document_processor.split_document(content, chunk_size, overlap)
        logger.info(f"文档已分割为 {len(chunks)} 个块")

        # 生成问答对
        all_qa_pairs = []
        for i, chunk in enumerate(chunks):
            logger.info(f"正在处理第 {i+1}/{len(chunks)} 个块")
            qa_pairs = self.qa_generator.generate_qa_pairs(chunk, self.prompt_template)
            all_qa_pairs.extend(qa_pairs)
            logger.info(f"从第 {i+1} 个块生成了 {len(qa_pairs)} 个问答对")

        # 生成输出文件名
        base_name = os.path.basename(file_path)
        file_name, _ = os.path.splitext(base_name)
        output_file = os.path.join(self.output_dir, f"{file_name}_qa.jsonl")

        # 写入JSONL文件
        self.jsonl_writer.write_jsonl(all_qa_pairs, output_file)

        return output_file


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='将文档转换为问答对JSONL文件')
    parser.add_argument('--file', type=str, required=True, help='输入文档文件路径')
    parser.add_argument('--chunk-size', type=int, default=1000, help='文档分块大小')
    parser.add_argument('--overlap', type=int, default=200, help='分块重叠大小')
    parser.add_argument('--output-dir', type=str, default='.', help='输出目录')
    return parser.parse_args()


if __name__ == "__main__":
    # 可变参数
    API_URL = "http://localhost:11434/api/generate"
    MODEL = "qwen2.5:latest"
    SUPPORTED_EXTENSIONS = ['.txt', '.md', '.text', '.markdown']
    PROMPT_TEMPLATE = """
    请根据以下文档内容，生成5个高质量的问答对。每个问答对应包含一个问题和一个详细的答案。
    问题应该涵盖文档中的重要概念、事实或观点，答案应该准确、全面且有信息量。

    文档内容:
    {document}

    请按照以下格式输出问答对:

    问题1: [问题内容]
    答案1: [答案内容]

    问题2: [问题内容]
    答案2: [答案内容]

    ...以此类推
    """
    OUTPUT_DIR = "."  # 默认输出到当前目录
    CHUNK_SIZE = 1000
    OVERLAP = 200

    # 解析命令行参数
    args = parse_arguments()

    # 创建文档转问答对处理器
    doc_to_qa = DocumentToQA(
        api_url=API_URL,
        model=MODEL,
        supported_extensions=SUPPORTED_EXTENSIONS,
        prompt_template=PROMPT_TEMPLATE,
        output_dir=args.output_dir or OUTPUT_DIR
    )

    # 处理文档
    output_file = doc_to_qa.process_document(
        file_path=args.file,
        chunk_size=args.chunk_size or CHUNK_SIZE,
        overlap=args.overlap or OVERLAP
    )

    print(f"处理完成，问答对已保存到: {output_file}")