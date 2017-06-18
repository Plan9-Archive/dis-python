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
    sys->print("Counting...\n");
    for (i := 0; i < 20; i++)
        sys->print("%d\n", i);
}
