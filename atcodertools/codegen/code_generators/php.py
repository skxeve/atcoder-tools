from typing import Dict, Any, Optional, List

from atcodertools.codegen.code_style_config import CodeStyleConfig
from atcodertools.codegen.models.code_gen_args import CodeGenArgs
from atcodertools.codegen.template_engine import render
from atcodertools.fmtprediction.models.format import Pattern, SingularPattern, ParallelPattern, TwoDimensionalPattern, \
    Format
from atcodertools.fmtprediction.models.type import Type
from atcodertools.fmtprediction.models.variable import Variable


def _loop_header(var: Variable, for_second_index: bool):
    if for_second_index:
        index = var.second_index
        loop_var = "j"
    else:
        index = var.first_index
        loop_var = "i"

    return "for (${loop_var} = 0; ${loop_var} < ${length}; ${loop_var}++) {open_brace}".format(
        loop_var=loop_var,
        length=index.get_length(),
        open_brace='{'
    )


class Php7CodeGenerator:

    def __init__(self,
                 format_: Optional[Format[Variable]],
                 config: CodeStyleConfig):
        self._format = format_
        self._config = config

    def generate_parameters(self) -> Dict[str, Any]:
        if self._format is None:
            return dict(prediction_success=False)

        return dict(input_part=self._input_part(),
                    prediction_success=True)

    def _convert_type(self, type_: Type) -> str:
        if type_ == Type.float:
            return "float"
        elif type_ == Type.int:
            return "int"
        elif type_ == Type.str:
            return "string"
        else:
            raise NotImplementedError

    def _input_part(self):
        lines = []
        for pattern in self._format.sequence:
            lines += self._render_pattern(pattern)
        return "\n{indent}".format(indent=self._indent(0)).join(lines)

    def _input_code_for_token(self, type_: Type) -> str:
        return "({type})getNext($gen);".format(type=self._convert_type(type_))

    def _input_code_for_whole_pattern(self, pattern: Pattern) -> List[str]:
        lines = []
        representative_var = pattern.all_vars()[0]

        if isinstance(pattern, SingularPattern):
            lines.append("${name} = {input_}".format(
                name=representative_var.name,
                input_=self._input_code_for_token(representative_var.type)))

        elif isinstance(pattern, ParallelPattern):
            lines.append(_loop_header(representative_var, False))
            for var in pattern.all_vars():
                lines.append("{indent}${name} = {input_}".format(indent=self._indent(1),
                                                                name=var.name,
                                                                input_=self._input_code_for_token(var.type)))
            lines.append("")
            lines.append("")
            lines.append("}")

        elif isinstance(pattern, TwoDimensionalPattern):
            lines.append(_loop_header(representative_var, False))
            lines.append(
                "{indent}${line}[]".format(indent=self._indent(1), line=_loop_header(representative_var, True)))
            for var in pattern.all_vars():
                lines.append("{indent}${name} = {input_}".format(indent=self._indent(2),
                                                                name=var.name,
                                                                input_=self._input_code_for_token(var.type)))
            lines.append("")
            lines.append("")
            lines.append("{indent}}".format(indent=self._indent(1)))
            lines.append("}")

        else:
            raise NotImplementedError
        return lines

    def _render_pattern(self, pattern: Pattern):
        return self._input_code_for_whole_pattern(pattern)

    def _indent(self, depth):
        return self._config.indent(depth)


def main(args: CodeGenArgs) -> str:
    code_parameters = Php7CodeGenerator(
        args.format, args.config).generate_parameters()
    return render(
        args.template,
        mod=args.constants.mod,
        yes_str=args.constants.yes_str,
        no_str=args.constants.no_str,
        **code_parameters
    )
