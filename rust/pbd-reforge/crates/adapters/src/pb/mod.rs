//! PowerBuilder Adapters

pub mod pbd_reader {
    //! PBD format reader with mmap

    use memmap2::Mmap;
    use std::fs::File;
    use std::path::Path;

    pub struct PbdReader {
        _mmap: Mmap,
    }

    impl PbdReader {
        pub fn open(path: &Path) -> std::io::Result<Self> {
            let file = File::open(path)?;
            let mmap = unsafe { Mmap::map(&file)? };
            Ok(Self { _mmap: mmap })
        }
    }
}

pub mod pbd_scanner {
    //! Signature scanning and heuristics
}

pub mod pb6_decoder {
    //! PowerBuilder 6.x decoder
}

pub mod pb12_decoder {
    //! PowerBuilder 12.x decoder
}

pub mod pb2019_decoder {
    //! PowerBuilder 2017/2019 decoder
}
