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

    return "for {loop_var} in range({length}):".format(
        loop_var=loop_var,
        length=index.get_length()
    )


class Php3CodeGenerator:

    def __init__(self,
                 format_: Optional[Format[Variable]],
                 config: CodeStyleConfig):
        self._format = format_
        self._config = config

    def generate_parameters(self) -> Dict[str, Any]:
        if self._format is None:
            return dict(prediction_success=False)

        return dict(formal_arguments=self._formal_arguments(),
                    actual_arguments=self._actual_arguments(),
                    input_part=self._input_part(),
                    prediction_success=True)

    def _input_part(self):
        lines = []
        for pattern in self._format.sequence:
            lines += self._render_pattern(pattern)
        return "\n{indent}".format(indent=self._indent(0)).join(lines)

    def _convert_type(self, type_: Type) -> str:
        if type_ == Type.float:
            return "float"
        elif type_ == Type.int:
            return "int"
        elif type_ == Type.str:
            return "string"
        else:
            raise NotImplementedError

    def _get_declaration_type(self, var: Variable):
        if var.dim_num():
            return 'array'
        else:
            return self._convert_type(var.type)

    def _actual_arguments(self) -> str:
        """
            :return the string form of actual arguments e.g. "N, K, a"
        """
        return "$" + ", $".join([v.name for v in self._format.all_vars()])

    def _formal_arguments(self):
        """
            :return the string form of formal arguments e.g. "N: int, K: int, a: List[int]"
        """
        return ", ".join([
            "{decl_type} ${name}".format(
                decl_type=self._get_declaration_type(v),
                name=v.name)
            for v in self._format.all_vars()
        ])

    def _generate_declaration(self, var: Variable):
        """
        :return: Create declaration part E.g. array[1..n] -> array = [int()] * (n-1+1)  # type: List[int]
        """
        if var.dim_num() == 0:
            dims = []
        elif var.dim_num() == 1:
            dims = [var.first_index.get_length()]
        elif var.dim_num() == 2:
            dims = [var.first_index.get_length(),
                    var.second_index.get_length()]
        else:
            raise NotImplementedError

        ctype = self._convert_type(var.type)
        if len(dims) == 0:
            ctor = "{}()".format(ctype)
        elif len(dims) == 1:
            ctor = "[{ctype}()] * ({dim})".format(ctype=ctype, dim=dims[0])
        else:
            ctor = "[{ctype}()] * ({dim})".format(ctype=ctype, dim=dims[0])
            for dim in dims[-2::-1]:
                ctor = "[{ctor} for _ in range({dim})]".format(
                    ctor=ctor, dim=dim)

        line = "{name} = {constructor}  # type: {decl_type} ".format(
            name=var.name,
            decl_type=self._get_declaration_type(var),
            constructor=ctor
        )
        return line

    def _input_code_for_token(self, type_: Type, name: str) -> str:
        if type_ == Type.float:
            return "fscanf(STDIN, '%f', ${name});".format(name=name)
        elif type_ == Type.int:
            return "fscanf(STDIN, '%d', ${name});".format(name=name)
        elif type_ == Type.str:
            return "fscanf(STDIN, '%s', ${name});".format(name=name)
        else:
            raise NotImplementedError

    def _input_code_for_single_pattern(self, pattern: Pattern) -> str:
        assert len(pattern.all_vars()) == 1
        var = pattern.all_vars()[0]

        if isinstance(pattern, SingularPattern):
            input_ = self._input_code_for_token(var.type, var.name)

        elif isinstance(pattern, ParallelPattern):
            input_ = "${name} = explode(' ', fgets(STDIN)); // {type_}".format(
                    name=var.name,
                    type_=self._get_declaration_type(var))

        elif isinstance(pattern, TwoDimensionalPattern):
            input_ = "foreach (array_chunk(explode(' ', fgets(STDIN)), 2) as $kv) { ${name}[$kv[0]] = $kv[1]; } // {type_}".format(
                    name=var.name,
                    type_=self._get_declaration_type(var))

        else:
            raise NotImplementedError

        return input_

    @staticmethod
    def _get_var_name(var: Variable):
        name = var.name
        if var.dim_num() >= 1:
            name += "[i]"
        if var.dim_num() >= 2:
            name += "[j]"
        return name

    def _input_code_for_non_single_pattern(self, pattern: Pattern) -> List[str]:
        lines = []
        for var in pattern.all_vars():
            lines.append(self._generate_declaration(var))
        representative_var = pattern.all_vars()[0]

        if isinstance(pattern, SingularPattern):
            assert False

        elif isinstance(pattern, ParallelPattern):
            lines.append(_loop_header(representative_var, False))
            for var in pattern.all_vars():
                lines.append("{indent}{name} = {input_}".format(indent=self._indent(1),
                                                                name=self._get_var_name(
                                                                    var),
                                                                input_=self._input_code_for_token(var.type)))

        elif isinstance(pattern, TwoDimensionalPattern):
            lines.append(_loop_header(representative_var, False))
            lines.append(
                "{indent}{line}".format(indent=self._indent(1), line=_loop_header(representative_var, True)))
            for var in pattern.all_vars():
                lines.append("{indent}{name} = {input_}".format(indent=self._indent(2),
                                                                name=self._get_var_name(
                                                                    var),
                                                                input_=self._input_code_for_token(var.type)))

        else:
            raise NotImplementedError
        return lines

    def _render_pattern(self, pattern: Pattern):
        if len(pattern.all_vars()) == 1:
            return [self._input_code_for_single_pattern(pattern)]
        else:
            return self._input_code_for_non_single_pattern(pattern)

    def _indent(self, depth):
        return self._config.indent(depth)


def main(args: CodeGenArgs) -> str:
    code_parameters = Php3CodeGenerator(
        args.format, args.config).generate_parameters()
    return render(
        args.template,
        mod=args.constants.mod,
        yes_str=args.constants.yes_str,
        no_str=args.constants.no_str,
        **code_parameters
    )
