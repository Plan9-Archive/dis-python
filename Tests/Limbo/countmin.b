implement count;

include "sys.m";
include "draw.m";

count: module
{
    init: fn(ctxt: ref Draw->Context, args: list of string);
};

init(ctxt: ref Draw->Context, args: list of string)
{
    sys := load Sys Sys->PATH;
    for (i := 0; i < 123; i++)
        ;
}
