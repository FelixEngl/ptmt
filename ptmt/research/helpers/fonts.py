import dataclasses
import typing
import matplotlib.pyplot as plt

def _create_default_rc(name: str) -> dataclasses.Field:
    return dataclasses.field(default_factory=lambda: plt.rcParams[name])


_ALLOWED_LITERAL = typing.Literal[
    'a', 'x', 'y', 'b', 't', 'l', 'r', 'f', 'bl', 'br', 'bt', 'lb', 'lr', 'lt', 'rb', 'rl', 'rt', 'tb', 'tl', 'tr', 'blr', 'blt', 'brl', 'brt', 'btl', 'btr', 'lbr', 'lbt', 'lrb', 'lrt', 'ltb', 'ltr', 'rbl', 'rbt', 'rlb', 'rlt', 'rtb', 'rtl', 'tbl', 'tbr', 'tlb', 'tlr', 'trb', 'trl', 'blrt', 'bltr', 'brlt', 'brtl', 'btlr', 'btrl', 'lbrt', 'lbtr', 'lrbt', 'lrtb', 'ltbr', 'ltrb', 'rblt', 'rbtl', 'rlbt', 'rltb', 'rtbl', 'rtlb', 'tblr', 'tbrl', 'tlbr', 'tlrb', 'trbl', 'trlb']


@dataclasses.dataclass
class FontSizes:
    x_label_bottom: int | str = _create_default_rc('axes.labelsize')
    x_label_top: int | str = _create_default_rc('axes.labelsize')
    y_label_left: int | str = _create_default_rc('axes.labelsize')
    y_label_right: int | str = _create_default_rc('axes.labelsize')
    x_ticks_bottom: int | str = _create_default_rc('xtick.labelsize')
    x_ticks_top: int | str = _create_default_rc('xtick.labelsize')
    y_ticks_left: int | str = _create_default_rc('ytick.labelsize')
    y_ticks_right: int | str = _create_default_rc('ytick.labelsize')
    legend_font: int | str | None = _create_default_rc('legend.fontsize')
    legend_title: int | str | None = _create_default_rc('legend.title_fontsize')

    def set_size(self, value: int | str, target: typing.Literal['label', 'ticks', 'legend'],
                 axis: _ALLOWED_LITERAL = 'a') -> 'FontSizes':
        match target:
            case 'label':
                match axis:
                    case 'a':
                        self.x_label_bottom = value
                        self.x_label_top = value
                        self.y_label_left = value
                        self.y_label_right = value
                    case 'x':
                        self.x_label_bottom = value
                        self.x_label_top = value
                    case 'y':
                        self.y_label_left = value
                        self.y_label_right = value
                    case other:
                        for k in other:
                            match k:
                                case 'b':
                                    self.x_label_bottom = value
                                case 't':
                                    self.x_label_top = value
                                case 'l':
                                    self.y_label_left = value
                                case 'r':
                                    self.y_label_right = value
                                case ukn:
                                    raise ValueError(f'"{ukn}" is not supported for {target}!')
            case 'ticks':
                match axis:
                    case 'a':
                        self.x_ticks_bottom = value
                        self.x_ticks_top = value
                        self.y_ticks_left = value
                        self.y_ticks_right = value
                    case 'x':
                        self.x_ticks_bottom = value
                        self.x_ticks_top = value
                    case 'y':
                        self.y_ticks_left = value
                        self.y_ticks_right = value
                    case other:
                        for k in other:
                            match k:
                                case 'b':
                                    self.x_ticks_bottom = value
                                case 't':
                                    self.x_ticks_top = value
                                case 'l':
                                    self.y_ticks_left = value
                                case 'r':
                                    self.y_ticks_right = value
                                case ukn:
                                    raise ValueError(f'"{ukn}" is not supported for {target}!')
            case 'legend':
                match axis:
                    case 'a' | 'tf' | 'ft':
                        self.legend_font = value
                        self.legend_title = value
                    case 'f':
                        self.legend_font = value
                    case 't':
                        self.legend_title = value
                    case ukn:
                        raise ValueError(f'"{ukn}" is not supported for {target}!')
        return self