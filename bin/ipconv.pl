#!/usr/bin/perl -w
use strict;
use Socket;

my %cache;

sub ip2host {
    my $ip = shift;
    return $cache{$ip} if exists $cache{$ip};
    if (my $h = gethostbyaddr(inet_aton($ip), AF_INET)) {
        $h =~ s/\.ps.easou.com$//;
        return $cache{$ip} = $h;
    }
    return $ip;
}

my $only = 0;
if (@ARGV && $ARGV[0] eq "-h") {
    print <<EOF;
Usage:
$0 -h
$0 [-o] [filename]
EOF
    exit;
} elsif (@ARGV && $ARGV[0] eq "-o") {
    $only = 1;
    shift @ARGV;
}

while (<>) {
    if (s/((\d{1,3}\.){3}\d{1,3})/ip2host($1)/eg || ! $only) {
        print;
    }
}
